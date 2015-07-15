import os, urllib, re

from settings import (BASE_PATH, DESKTOP_MODE, STATIC_PATH, PRODUCT_NAME,
    APPLICATION_PATH, DEFAULT_LOCAL_ADDRESS, DEFAULT_LOCAL_PORT, 
    SECRET_KEY, _sep)

from core import (cms, mgmt, ui, auth)

from core.libs.bottle import (Bottle, static_file, request, response, abort, template)

from core.models import (db, get_blog, get_media,FileInfo)
from core.error import (UserNotFound, CSRFTokenNotFound)
from core.utils import csrf_hash


app = Bottle()
_route = app.route
_hook = app.hook

# any theme-based routes will be set up here
# /blog/x/<path:path> -- for non-greedy matching

@_route(BASE_PATH + "/system/theme/<blog_id:int>")
def export_theme(blog_id):
    from core import theme
    return theme.export_theme_for_blog(blog_id)

def setup(step_id=None):
    if step_id is None:
        step_id = 0
    
    # TODO: also attempt to fetch step ID from ini file
    from install import install
    return install.step(step_id)
    
@_hook('before_request')
def strip_path():
    # Removes trailing slashes from a URL before processing
    if len(request.environ['PATH_INFO']) > 1:
        request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')
        
@_hook('before_request')
def csrf_protection():
    # Form protection from CSRF attacks. DON'T EVER DISABLE THIS
    if request.method == "POST":
        
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

@_route(BASE_PATH + "/system/sites")
def site_list():
    return ui.system_sites()

# TODO: the default should be whatever editor theme is installed by the current blog theme
@_route(BASE_PATH + "/blog/<blog_id:int>/editor-css")
def css(blog_id):
    blog = get_blog(blog_id)
    if blog.editor_css is None:
        from core import static
        template = static.editor_css 
    else:
        template = blog.editor_css
    response.content_type = "text/css"
    response.add_header('Cache-Control', 'max-age=7200')
    return template

@_route(BASE_PATH + "/system/plugins")
def system_plugins():
    return ui.system_plugins()

@_route(BASE_PATH + "/system/plugins/<plugin_id:int>")
def plugin_settings(plugin_id):
    pass

@_route(BASE_PATH + "/system/info")
def site_info():
    return ui.system_info()

@_route(BASE_PATH + "/system/plugins/<plugin_id:int>/enable")
def enable_plugin(plugin_id):
    from core.plugins import enable_plugin
    enable_plugin(plugin_id)

@_route(BASE_PATH + "/system/plugins/<plugin_id:int>/disable")
def disable_plugin(plugin_id):
    from core.plugins import disable_plugin
    disable_plugin(plugin_id)

@_route(BASE_PATH + '/test/<blog_id:int>')
def test_function(blog_id):
    db.connect()
    with db.atomic():
        blog = get_blog(blog_id)
        f_n = cms.purge_blog_(blog)
    db.close()
    return f_n

@_route(BASE_PATH + '/login')
def login():
    return ui.login()

@_route(BASE_PATH + '/login', method='POST')
def login_verify():
    return ui.login_verify()

@_route(BASE_PATH + '/logout')
def logout():
    return ui.logout()

@_route('/')
@_route(BASE_PATH)
def main_ui():
    return ui.main_ui()

@_route(BASE_PATH + '/site/<site_id:int>')
def site(site_id):
    return ui.site(site_id)

@_route(BASE_PATH + "/system/plugins/register/<plugin_path>")
def register_plugin(plugin_path):
    return ui.register_plugin(plugin_path)

@_route(BASE_PATH + "/system/queue")
def system_queue():
    return ui.system_queue()

@_route(BASE_PATH + "/system/log")
def system_log():
    return ui.system_log()

@_route(BASE_PATH + '/site/<site_id:int>/blogs')
def site_blogs(site_id):
    return ui.site(site_id)

@_route(BASE_PATH + '/site/<site_id:int>/create-blog')
def blog_create(site_id):
    return ui.blog_create(site_id)

@_route(BASE_PATH + '/site/<site_id:int>/create-blog', method='POST')
def blog_create_save(site_id):
    return ui.blog_create_save(site_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/create-user')
def blog_create_user(blog_id):
    return ui.blog_create_user(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/create-user', method='POST')
def blog_create_user_save(blog_id):
    return ui.blog_create_user_save(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/user/<user_id:int>')
def blog_user_edit(blog_id, user_id):
    return ui.blog_user_edit(blog_id, user_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/user/<user_id:int>', method='POST')
def blog_user_edit_save(blog_id, user_id):
    return ui.blog_user_edit_save(blog_id, user_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/users')
def blog_list_users(blog_id):
    return ui.blog_list_users(blog_id)

@_route(BASE_PATH + '/site/<site_id:int>/users')
def site_list_users(site_id):
    return ui.site_list_users(site_id)

@_route(BASE_PATH + '/site/<site_id:int>/create-user')
def site_create_user(site_id):
    return ui.site_create_user(site_id)

@_route(BASE_PATH + '/site/<site_id:int>/create-user', method='POST')
def site_create_user_save(site_id):
    return ui.site_create_user_save(site_id)

@_route(BASE_PATH + '/site/<site_id:int>/user/<user_id:int>')
def site_edit_user(site_id, user_id):
    return ui.site_edit_user(site_id, user_id)

@_route(BASE_PATH + '/site/<site_id:int>/user/<user_id:int>', method='POST')
def site_edit_user_save(site_id, user_id):
    return ui.site_edit_user_save(site_id, user_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/newpage')
def blog_new_page(blog_id):
    return ui.blog_new_page(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/newpage', method='POST')
def blog_new_page_save(blog_id):
    return ui.blog_new_page_save(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>')
def blog(blog_id, errormsg=None):
    return ui.blog(blog_id, errormsg)

@_route(BASE_PATH + '/template/<template_id:int>/edit')
def template_edit(template_id):
    return ui.template_edit(template_id)

@_route(BASE_PATH + '/template/<template_id:int>/edit', method="POST")
def template_edit_save(template_id):
    return ui.template_edit_save(template_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/tag/<tag_id:int>')
@_route(BASE_PATH + '/blog/<blog_id:int>/tag/<tag_id:int>', method='POST')
def edit_tag(blog_id, tag_id):
    return ui.edit_tag(blog_id, tag_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/tags')
def blog_tags(blog_id):
    return ui.blog_tags(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/media')
def blog_media(blog_id):
    return ui.blog_media(blog_id)
    
@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/edit')
def blog_media_edit(blog_id, media_id):
    return ui.blog_media_edit(blog_id, media_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/edit', method='POST')
def blog_media_edit_save(blog_id, media_id):
    return ui.blog_media_edit_save(blog_id, media_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/delete')
@_route(BASE_PATH + '/blog/<blog_id:int>/media/<media_id:int>/delete', method="POST")
def blog_media_delete(blog_id, media_id):
    return ui.blog_media_delete(blog_id, media_id)
        
@_route(BASE_PATH + '/blog/<blog_id:int>/templates')
def blog_templates(blog_id):
    return ui.blog_templates(blog_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit')
def page_edit(page_id):
    return ui.page_edit(page_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit', method='POST')
def page_edit_save(page_id):
    return ui.page_edit_save(page_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit/revisions')
def page_revisions(page_id):
    return ui.page_revisions(page_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit/restore/<revision_id>')
def page_revision_restore(page_id, revision_id):
    return ui.page_revision_restore(page_id, revision_id)

@_route(BASE_PATH + '/page/<page_id:int>/edit/restore/<revision_id>', method='POST')
def page_revision_restore_save(page_id, revision_id):  # @UnusedVariable
    return ui.page_revision_restore_save(page_id)

@_route(BASE_PATH + '/page/<page_id:int>/upload', method='POST')
def page_media_upload(page_id):
    return ui.page_media_upload(page_id)

@_route(BASE_PATH + '/page/<page_id:int>/media/<media_id:int>/delete', method='POST')
def page_media_delete(page_id, media_id):
    return ui.page_media_delete(page_id, media_id)

'''
EXAMPLE OF A MODAL FUNCTION
@_route(BASE_PATH + '/page/<page_id:int>/media/<media_id>/edit')
def page_media_edit(page_id, media_id):
    return ui.page_media_edit(page_id, media_id)
'''

@_route(BASE_PATH + '/blog/<blog_id:int>/republish')
def blog_republish(blog_id):
    return ui.blog_republish(blog_id)

@_route(BASE_PATH + '/blog/<blog_id:int>/purge')
def blog_purge(blog_id):
    return ui.blog_purge(blog_id)

# temporary
@_route(BASE_PATH + '/page/<page_id:int>/del')
@_route(BASE_PATH + '/page/<page_id:int>/delete', method='POST')
def page_delete(page_id):
    return ui.page_delete(page_id)

@_route(BASE_PATH + '/export')
def export_data():
    return mgmt.export_data()

@_route(BASE_PATH + '/import')
def import_data():
    return mgmt.import_data()
    
@_route(BASE_PATH + "/blog/<blog_id:int>/queue")
def blog_queue(blog_id):
    return ui.blog_queue(blog_id)

@_route(BASE_PATH + "/blog/<blog_id:int>/settings")
def blog_settings(blog_id,):
    return ui.blog_settings(blog_id)
    
@_route(BASE_PATH + "/blog/<blog_id:int>/settings", method='POST')
def blog_settings_save(blog_id):
    return ui.blog_settings_save(blog_id)
    
@_route(BASE_PATH + "/blog/<blog_id:int>/publish")
def blog_publish(blog_id):
    return ui.blog_publish(blog_id)
    
@_route(BASE_PATH + "/blog/<blog_id:int>/publish/progress/<original_queue_length:int>")
def blog_publish_progress(blog_id, original_queue_length):
    return ui.blog_publish_progress(blog_id, original_queue_length)

@_route(BASE_PATH + "/blog/<blog_id:int>/publish/process")
def blog_publish_process(blog_id):
    return ui.blog_publish_process(blog_id)
    # TODO: do we still need this?


@_route(BASE_PATH + "/page/<page_id:int>/preview")
def page_preview(page_id):
    return ui.page_preview(page_id)

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
    
    page = FileInfo.get(
        FileInfo.url==path)
    
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
            abort(404, 'File not found')
    
        k = static_file(filesystem_filepath, root=root_path)
        
        if (k.headers['Content-Type'][:5] == "text/" or 
            k.headers['Content-Type'] == "application/javascript"):
            
            k.add_header('Cache-Control', 'max-age=7200, public, must-revalidate')
    
        if (k._headers['Content-Type'][0][:5] == "text/" and not k.body == ""):
    
            x = k.body.read()
            k.body.close()
            
            y = x.decode('utf8')
            z = re.compile(r' href=["\']' + (blog.url) + '([^"\']*)["\']')
            y = re.sub(z, r" href='http://" + DEFAULT_LOCAL_ADDRESS + DEFAULT_LOCAL_PORT + "\\1\?_=1'", y)           
            y = y.encode('utf8')
    
            k.headers['Content-Length'] = len(y)
            k.body = y
    
        return (k)

    def system_site_index():
        from core.models import Site
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
        
    
@_route(BASE_PATH + STATIC_PATH + '/<filepath:path>')
def server_static(filepath):
    '''
    Serves static files from the application's own internal static path,
    e.g. for its CSS/JS 
    '''
    
    response.add_header('Cache-Control', 'max-age=7200')
    return static_file(filepath, root=APPLICATION_PATH + STATIC_PATH)

# if DEBUG_MODE is False:
@app.error(500)
def error_handler(error):
    import settings as _settings
    tpl = template('500_error',
        settings=_settings,
        error=error)
    
    if error.exception.__class__ == CSRFTokenNotFound:
        response.status = '401 CSRF token not found'
    return tpl

@_route(BASE_PATH + '/page/<page_id:int>/get-media-templates/<media_id:int>')
def page_get_media_templates(page_id, media_id):
    return ui.page_get_media_templates(page_id, media_id)

@_route(BASE_PATH + '/page/<page_id:int>/add-media/<media_id:int>/<template_id:int>')
def page_add_media_with_template(page_id, media_id, template_id):
    return ui.page_add_media_with_template(page_id, media_id, template_id)

@_route(BASE_PATH + "/api/1/get-tag/<tag_name>")
def api_get_tag(tag_name):
    return ui.get_tag(tag_name)

# TODO: make /page/<>/generate-tag when we rewrite the underlying routine
# no need for an api path here?
# for apis might want to use a variable, pass that to a control array
 
@_route(BASE_PATH + "/api/1/make-tag-for-page/blog/<blog_id:int>", method='POST')
@_route(BASE_PATH + "/api/1/make-tag-for-page/page/<page_id:int>", method='POST')
def api_make_tag_for_page(blog_id=None, page_id=None):
    return ui.make_tag_for_page(blog_id, page_id)



'''
@_route(BASE_PATH+"/api/1/remove-tag-from-page/<page_id:int>/<tag_id:int>", method='POST')
def api_remove_tag_from_page(tag_id, page_id):
    return ui.remove_tag_from_page(tag_id, page_id)
'''
