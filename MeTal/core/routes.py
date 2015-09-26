import os, re, urllib

from core import (mgmt, auth)
from core.error import (UserNotFound, CSRFTokenNotFound)
from core.libs.bottle import (Bottle, static_file, request, response, abort)
from core.models import (db, get_page, get_blog, get_theme, get_media, FileInfo)
from core.utils import csrf_hash, raise_request_limit
from settings import (BASE_PATH, DESKTOP_MODE, STATIC_PATH, PRODUCT_NAME,
                      APPLICATION_PATH, DEFAULT_LOCAL_ADDRESS, DEFAULT_LOCAL_PORT,
                      SECRET_KEY, _sep)


app = Bottle()
_route = app.route
_hook = app.hook

# use this pattern for breaking up the router into multiple modules later on?
'''
@_route(BASE_PATH + "/t1")
def t1():
    return "T1"

@_route(BASE_PATH + "/t1/<path>")
def t(path):
    print ("t")

    @_route(BASE_PATH + "/t1/t2")
    def t2():
        print ("t2")
        return "T2"

    return app.router.match(request)[0]()
'''


@_hook('before_request')
def strip_path():
    '''
    Removes trailing slashes from a URL before processing.
    '''
    if len(request.environ['PATH_INFO']) > 1:
        request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')


@_hook('before_request')
def csrf_protection():
    '''
    Adds CSP headers to requests by default, and checks for the presence of
    CSRF protection in submitted forms.
    '''
    response.add_header('Frame-Options', 'sameorigin')
    # response.add_header('Content-Security-Policy', "default-src 'self' 'unsafe-inline' 'unsafe-eval'")

    if request.method == "POST":
        raise_request_limit()
        try:
            user = auth.is_logged_in_core(request)
        except UserNotFound:
            csrf_code = csrf_hash(SECRET_KEY)
            user = None
        else:
            csrf_code = csrf_hash(user.last_login)

        if request.forms.getunicode('csrf') != csrf_code:
            raise CSRFTokenNotFound("Form submitted from {} did not have a valid CSRF protection token.".format(
                request.url))


@_route(BASE_PATH + STATIC_PATH + '/<filepath:path>')
def server_static(filepath):
    '''
    Serves static files from the application's own internal static path,
    e.g. for its CSS/JS
    '''
    response.add_header('Cache-Control', 'max-age=7200')
    return static_file(filepath, root=APPLICATION_PATH + STATIC_PATH)

@_route(BASE_PATH + "/blog/<blog_id:int>/erase-queue")
def erase_queue(blog_id):
    blog = get_blog(blog_id)
    from core.models import Queue
    delete_queue = Queue.delete().where(Queue.blog == blog)
    delete_queue.execute()
    return "Queue for blog {} erased".format(blog.id)

@_route(BASE_PATH + "/blog/<blog_id:int>/delete")
def delete_blog(blog_id):
    with db.atomic():
        blog = get_blog(blog_id)
        blog.delete_instance(recursive=True)
    return "Blog {} deleted".format(blog_id)

@_route(BASE_PATH + "/page/<page_id:int>/reparent/<blog_id:int>")
def reparent_page(page_id, blog_id):
    with db.atomic():
        page = get_page(page_id)
        blog = get_blog(blog_id)
        page.blog = blog.id
        page.text += "\n"  # stupid hack, we should have a force-save option
        # also, have .save options kw, not args

        # Reparent any existing media
        # Delete any existing categories
        # Migrate/re-add any existing tags
        # Remove and regenerate basename, permalink, etc.
        # Create new fileinfo

        from core.error import PageNotChanged
        try:
            page.save(page.user)
        except PageNotChanged:
            pass
    return "OK"
    # redirect(BASE_URL + '/page/{}/edit'.format(page.id))

@_route(BASE_PATH + "/theme/<theme_id:int>/refresh-theme")
def refresh_theme(theme_id):
    '''
    imports JSON and refreshes the selected theme with it
    '''
    with open(APPLICATION_PATH + _sep + 'install' + _sep +
        'templates.json' , "r", encoding='utf-8') as input_file:
        theme_string = input_file.read()

    with db.atomic():
        theme = get_theme(theme_id)
        theme.json = theme_string
        theme.save()

@_route(BASE_PATH + "/blog/<blog_id:int>/overwrite-theme")
def overwrite_blog_theme(blog_id):
    '''
    imports JSON and overwrites an existing blog's theme
    '''
    user = auth.is_logged_in(request)

    with open(APPLICATION_PATH + _sep + 'install' + _sep +
        'templates.json' , "r", encoding='utf-8') as input_file:
        theme_string = input_file.read()

    # from core.models import get_default_theme, Struct
    from core.models import Struct
    # theme = get_default_theme()
    theme = Struct()
    theme.id = None
    theme.json = theme_string
    blog = get_blog(blog_id)
    from core import cms
    from core.auth import get_users_with_permission, role
    with db.atomic():
        cms.purge_fileinfos(blog.fileinfos)
        mgmt.erase_theme(blog)
        mgmt.theme_install_to_blog(theme, blog, user)


@_route(BASE_PATH + "/blog/<blog_id:int>/import-theme/<theme_id:int>")
def import_theme_to_blog(theme_id, blog_id):
    blog = get_blog(blog_id)
    old_theme = get_theme(theme_id)
    # this needs rewriting.
    # new_theme = mgmt.theme_install_to_blog(blog)
    # mgmt.theme_install_to_blog(new_theme, blog)
    # mgmt.theme_delete(old_theme)

    # when replacing a theme:
    # all Theme KV objects should be marked and reparented
    # perhaps we should specify the Theme head KV with a name
    # so that way we can match the name against the theme itself, too
    # have an option to force-delete

    # should we create an entirely new instance?
    # how do we distinguish between multiple instances of the same theme?

    # load in new theme from json in file somewhere, or maybe via a POST
    # register new theme with site
    # apply new theme to blog

    # rebuild all fileinfos = purge function


@_route(BASE_PATH + "/blog/<blog_id:int>/export-theme")
def export_theme(blog_id):
    from core import theme
    return theme.export_theme_for_blog(blog_id)


def setup(step_id=None):
    if step_id is None:
        step_id = 0
    # TODO: also attempt to fetch step ID from ini file
    from install import install
    return install.step(step_id)


@_route(BASE_PATH + "/system/sites")
def site_list():
    from core.ui import system
    return system.system_sites()


@_route(BASE_PATH + "/system/plugins")
def system_plugins():
    from core.ui import system
    return system.system_plugins()


@_route(BASE_PATH + "/system/plugins/<plugin_id:int>")
def plugin_settings(plugin_id):
    pass


@_route(BASE_PATH + "/system/info")
def site_info():
    from core.ui import system
    return system.system_info()


@_route(BASE_PATH + "/system/plugins/<plugin_id:int>/enable")
def enable_plugin(plugin_id):
    from core.plugins import enable_plugin
    enable_plugin(plugin_id)


@_route(BASE_PATH + "/system/plugins/<plugin_id:int>/disable")
def disable_plugin(plugin_id):
    from core.plugins import disable_plugin
    disable_plugin(plugin_id)


'''

@_route(BASE_PATH + '/test/<blog_id:int>')
def test_function(blog_id):
    with db.atomic():
        from core.models import Media
        from os import remove as _remove
        media_list = Media.select().where(
            Media.id > 3)
        n = ""
        for x in media_list:
            n += str(x.id) + ","
            try:
                _remove(x.path)
            except:
                pass
            x.delete_instance(recursive=True,
                delete_nullable=True)
    return n
'''


@_route(BASE_PATH + '/blog/<blog_id:int>/apply-theme/<theme_id:int>')
def apply_theme_test(blog_id, theme_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    theme = get_theme(theme_id)
    with db.atomic():
        n = mgmt.theme_apply_to_blog(theme, blog, user)
    return n


@_route(BASE_PATH + '/login')
def login():
    from core.ui import login
    return login.login()


@_route(BASE_PATH + '/login', method='POST')
def login_verify():
    from core.ui import login
    return login.login_verify()


@_route(BASE_PATH + '/logout')
def logout():
    from core.ui import login
    return login.logout()


@_route('/')
@_route(BASE_PATH)
def main_ui():
    from core.ui import login
    return login.main_ui()


@_route(BASE_PATH + '/site/<site_id:int>')
def site(site_id):
    from core.ui import ui
    return ui.site(site_id)


@_route(BASE_PATH + "/system/plugins/register/<plugin_path>")
def register_plugin(plugin_path):
    from core.ui import ui
    return ui.register_plugin(plugin_path)


@_route(BASE_PATH + "/system/queue")
def system_queue():
    from core.ui import system
    return system.system_queue()


@_route(BASE_PATH + "/system/log")
def system_log():
    from core.ui import system
    return system.system_log()


@_route(BASE_PATH + '/export')
def system_export_data():

    return mgmt.export_data()


@_route(BASE_PATH + '/import')
def system_import_data():
    return mgmt.import_data()


@_route(BASE_PATH + '/site/<site_id:int>/blogs')
def site_blogs(site_id):
    from core.ui import site
    return site.site(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/create-blog')
def site_blog_create(site_id):
    from core.ui import blog
    return blog.blog_create(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/create-blog', method='POST')
def site_blog_create_save(site_id):
    from core.ui import blog
    return blog.blog_create_save(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/users')
def site_list_users(site_id):
    from core.ui import site
    return site.site_list_users(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/create-user')
def site_create_user(site_id):
    from core.ui import site
    return site.site_create_user(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/create-user', method='POST')
def site_create_user_save(site_id):
    from core.ui import site
    return site.site_create_user_save(site_id)


@_route(BASE_PATH + '/site/<site_id:int>/user/<user_id:int>')
def site_edit_user(site_id, user_id):
    from core.ui import site
    return site.site_edit_user(site_id, user_id)


@_route(BASE_PATH + '/site/<site_id:int>/user/<user_id:int>', method='POST')
def site_edit_user_save(site_id, user_id):
    from core.ui import site
    return site.site_edit_user_save(site_id, user_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/create-user')
def blog_create_user(blog_id):
    from core.ui import blog
    return blog.blog_create_user(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/create-user', method='POST')
def blog_create_user_save(blog_id):
    from core.ui import blog
    return blog.blog_create_user_save(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/user/<user_id:int>')
def blog_user_edit(blog_id, user_id):
    from core.ui import blog
    return blog.blog_user_edit(blog_id, user_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/user/<user_id:int>', method='POST')
def blog_user_edit_save(blog_id, user_id):
    from core.ui import blog
    return blog.blog_user_edit_save(blog_id, user_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/users')
def blog_list_users(blog_id):
    from core.ui import blog
    return blog.blog_list_users(blog_id)

# TODO: the default should be whatever editor theme is installed by the
# current blog theme


@_route(BASE_PATH + "/blog/<blog_id:int>/editor-css")
def blog_editor_css(blog_id):
    blog = get_blog(blog_id)
    if blog.editor_css is None:
        from core import static
        template = static.editor_css
    else:
        template = blog.editor_css
    response.content_type = "text/css"
    response.add_header('Cache-Control', 'max-age=7200')
    return template


@_route(BASE_PATH + '/blog/<blog_id:int>/newpage')
def blog_new_page(blog_id):
    from core.ui import blog
    return blog.blog_new_page(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/newpage', method='POST')
def blog_new_page_save(blog_id):
    from core.ui import blog
    return blog.blog_new_page_save(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>')
def blog(blog_id, errormsg=None):
    from core.ui import blog
    return blog.blog(blog_id, errormsg)


@_route(BASE_PATH + '/blog/<blog_id:int>/tag/<tag_id:int>')
@_route(BASE_PATH + '/blog/<blog_id:int>/tag/<tag_id:int>', method='POST')
def blog_edit_tag(blog_id, tag_id):
    from core.ui import ui
    return ui.edit_tag(blog_id, tag_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/tags')
def blog_tags(blog_id):
    from core.ui import blog
    return blog.blog_tags(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/media')
def blog_media(blog_id):
    from core.ui import blog
    return blog.blog_media(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/edit')
def blog_media_edit(blog_id, media_id):
    from core.ui import blog
    return blog.blog_media_edit(blog_id, media_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/edit', method='POST')
def blog_media_edit_save(blog_id, media_id):
    from core.ui import blog
    return blog.blog_media_edit_save(blog_id, media_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/delete')
def blog_media_delete(blog_id, media_id):
    from core.ui import blog
    return blog.blog_media_delete(blog_id, media_id, None)


@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/delete', method="POST")
def blog_media_delete_confirm(blog_id, media_id):
    from core.ui import blog
    return blog.blog_media_delete(blog_id, media_id, request.forms.get('confirm'))


@_route(BASE_PATH + '/blog/<blog_id:int>/templates')
def blog_templates(blog_id):
    from core.ui import blog
    return blog.blog_templates(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/newtemplate/<template_type>')
def template_new(blog_id, template_type):
    from core.ui import template
    return template.new_template(blog_id, template_type)


@_route(BASE_PATH + '/template/<template_id:int>/edit')
def template_edit(template_id):
    from core.ui import template
    return template.template_edit(template_id)


@_route(BASE_PATH + '/template/<template_id:int>/edit', method="POST")
def template_edit_save(template_id):
    from core.ui import template
    return template.template_edit_save(template_id)

@_route(BASE_PATH + '/template/<template_id:int>/preview')
def template_preview(template_id):
    from core.ui import template
    return template.template_preview(template_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit')
def page_edit(page_id):
    from core.ui import ui
    return ui.page_edit(page_id)


@_route(BASE_PATH + '/page/<page_id:int>/edit', method='POST')
def page_edit_save(page_id):
    from core.ui import ui
    return ui.page_edit_save(page_id)


@_route(BASE_PATH + '/page/<page_id:int>/edit/revisions')
def page_revisions(page_id):
    from core.ui import ui
    return ui.page_revisions(page_id)


@_route(BASE_PATH + '/page/<page_id:int>/edit/restore/<revision_id>')
def page_revision_restore(page_id, revision_id):
    from core.ui import ui
    return ui.page_revision_restore(page_id, revision_id)


@_route(BASE_PATH + '/page/<page_id:int>/edit/restore/<revision_id>', method='POST')
def page_revision_restore_save(page_id, revision_id):  # @UnusedVariable
    from core.ui import ui
    return ui.page_revision_restore_save(page_id)


@_route(BASE_PATH + '/page/<page_id:int>/upload', method='POST')
def page_media_upload(page_id):
    from core.ui import ui
    return ui.page_media_upload(page_id)


@_route(BASE_PATH + '/page/<page_id:int>/media/<media_id:int>/delete', method='POST')
def page_media_delete(page_id, media_id):
    from core.ui import ui
    return ui.page_media_delete(page_id, media_id)

'''
EXAMPLE OF A MODAL FUNCTION
@_route(BASE_PATH + '/page/<page_id:int>/media/<media_id>/edit')
def page_media_edit(page_id, media_id):
    return ui.page_media_edit(page_id, media_id)
'''


@_route(BASE_PATH + '/blog/<blog_id:int>/republish')
def blog_republish(blog_id):
    from core.ui import blog
    return blog.blog_republish(blog_id)


@_route(BASE_PATH + '/blog/<blog_id:int>/purge')
def blog_purge(blog_id):
    from core.ui import blog
    return blog.blog_purge(blog_id)

# temporary


@_route(BASE_PATH + '/page/<page_id:int>/del')
@_route(BASE_PATH + '/page/<page_id:int>/delete', method='POST')
def page_delete(page_id):
    from core.ui import ui
    return ui.page_delete(page_id)


@_route(BASE_PATH + "/blog/<blog_id:int>/queue")
def blog_queue(blog_id):
    from core.ui import blog
    return blog.blog_queue(blog_id)


@_route(BASE_PATH + "/blog/<blog_id:int>/settings")
def blog_settings(blog_id,):
    from core.ui import blog
    return blog.blog_settings(blog_id)


@_route(BASE_PATH + "/blog/<blog_id:int>/settings", method='POST')
def blog_settings_save(blog_id):
    from core.ui import blog
    return blog.blog_settings_save(blog_id)


@_route(BASE_PATH + "/blog/<blog_id:int>/publish")
def blog_publish(blog_id):
    from core.ui import blog
    return blog.blog_publish(blog_id)


@_route(BASE_PATH + "/blog/<blog_id:int>/publish/progress/<original_queue_length:int>")
def blog_publish_progress(blog_id, original_queue_length):
    from core.ui import blog
    return blog.blog_publish_progress(blog_id, original_queue_length)


@_route(BASE_PATH + "/blog/<blog_id:int>/publish/process")
def blog_publish_process(blog_id):
    from core.ui import blog
    return blog.blog_publish_process(blog_id)
    # TODO: do we still need this?


@_route(BASE_PATH + "/page/<page_id:int>/preview")
def page_preview(page_id):
    from core.ui import ui
    return ui.page_preview(page_id)

@_route(BASE_PATH + "/page/<page_id:int>/delete-preview")
def delete_page_preview(page_id):
    from core.ui import ui
    return ui.delete_page_preview(page_id)

@_route(BASE_PATH + "/page/<page_id:int>/public-preview")
def page_public_preview(page_id):
    from core.ui import ui
    return ui.page_public_preview(page_id)

'''
Static routing.
'''


@_route(BASE_PATH + '/media/<media_id:int>')
def media_preview(media_id):

    media = get_media(media_id)
    try:
        root = media.path.rsplit(_sep, 1)[0]
    except:
        root = ''
    preview = static_file(media.filename, root=root)

    return preview


@_route('/preview/<path:path>')
def preview(path):

    from core.ui import ui

    page = FileInfo.get(
        FileInfo.url == path)

    # return template mapping if no page found

    # prefix urls in preview for virtual filesystem movement

    return ui.page_preview(page.page.id)


if DESKTOP_MODE:

    @_route('/')
    def blog_root():
        '''
        Returns the root directory for the currently previewed blog.
        '''
        return blog_static('index.html')

    @_route("<:re:(?!" + BASE_PATH + "/)><filepath:path>")
    def blog_static(filepath):
        '''
        Returns static routes for the currently staged blog.
        The blog ID is appended to the URL as a '_' parameter (e.g., ?_=1 for blog ID 1)
        The future of this function is currently being debated.
        '''

        try:
            blog_id = int(request.query['_'])
        except KeyError:
            return system_site_index()
            # raise

        blog = get_blog(blog_id)

        root_path = blog.path

        filesystem_filepath = urllib.parse.quote(filepath)

        # TODO: replace this with results from /preview path,
        # or another function that finds by abs path in db.

        if os.path.isfile(root_path + "/" + filesystem_filepath) is False:
            filepath += ("index.html")

        if os.path.isfile(root_path + "/" + filesystem_filepath) is False:

            abort(404, 'File {} not found'.format(root_path + "/" + filesystem_filepath))

        k = static_file(filesystem_filepath, root=root_path)

        if (k.headers['Content-Type'][:5] == "text/" or
                k.headers['Content-Type'] == "application/javascript"):

            k.add_header(
                'Cache-Control', 'max-age=7200, public, must-revalidate')

        if (k._headers['Content-Type'][0][:5] == "text/" and not k.body == ""):

            x = k.body.read()
            k.body.close()

            y = x.decode('utf8')
            z = re.compile(r' href=["\']' + (blog.url) + '([^"\']*)["\']')
            z2 = re.compile(r' href=["\'](/[^"\']*)["\']')
            y = re.sub(z, r" href='http://" + DEFAULT_LOCAL_ADDRESS +
                       DEFAULT_LOCAL_PORT + "\\1?_={}'".format(blog_id), y)
            y = re.sub(z2, r" href='\1?_={}'".format(blog_id), y)
            y = y.encode('utf8')

            k.headers['Content-Length'] = len(y)
            k.body = y

        return (k)

    def system_site_index():
        from core.models import Site
        from core.libs.bottle import template
        sites = Site.select()

        tpl = '''
<p>This is the local web server for an installation of {}.
<p><a href='{}'>Open the site dashboard</a>
<hr/>
<p>You can also preview sites and blogs available on this server:
<ul>'''.format(PRODUCT_NAME, BASE_PATH) + '''
% for site in sites:
    <li>{{site.name}}</li>
    % if site.blogs.count()>0:
        <ul>
        % for blog in site.blogs:
        % if blog.published_pages().count()>0:
            <li><a href="/?_={{blog.id}}">{{blog.name}}</a></li>
        % else:
        <li>{{blog.name}} [No published pages on this blog]</li>
        % end
        % end
        </ul>
    % end
%end
</ul><hr/>
'''
        return template(tpl, sites=sites)


# if DEBUG_MODE is False:
@app.error(500)
def error_handler(error):
    from core.libs.bottle import template
    import settings as _settings
    tpl = template('500_error',
                   settings=_settings,
                   error=error)

    if error.exception.__class__ == CSRFTokenNotFound:
        response.status = '401 CSRF token not found'
    return tpl


@_route(BASE_PATH + '/page/<page_id:int>/get-media-templates/<media_id:int>')
def page_get_media_templates(page_id, media_id):
    from core.ui import ui
    return ui.page_get_media_templates(page_id, media_id)


@_route(BASE_PATH + '/page/<page_id:int>/add-media/<media_id:int>/<template_id:int>')
def page_add_media_with_template(page_id, media_id, template_id):
    from core.ui import ui
    return ui.page_add_media_with_template(page_id, media_id, template_id)


@_route(BASE_PATH + "/api/1/get-tag/<tag_name>")
def api_get_tag(tag_name):
    from core.ui import ui
    return ui.get_tag(tag_name)

# TODO: make /page/<>/generate-tag when we rewrite the underlying routine
# no need for an api path here?
# for apis might want to use a variable, pass that to a control array


@_route(BASE_PATH + "/api/1/make-tag-for-page/blog/<blog_id:int>", method='POST')
@_route(BASE_PATH + "/api/1/make-tag-for-page/page/<page_id:int>", method='POST')
def api_make_tag_for_page(blog_id=None, page_id=None):
    from core.ui import ui
    return ui.make_tag_for_page(blog_id, page_id)

'''
@_route(BASE_PATH+"/api/1/remove-tag-from-page/<page_id:int>/<tag_id:int>", method='POST')
def api_remove_tag_from_page(tag_id, page_id):
    return ui.remove_tag_from_page(tag_id, page_id)
'''
