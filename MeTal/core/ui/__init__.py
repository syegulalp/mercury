from core import (auth, mgmt, utils, cms, ui_mgr, template as _template)
from core.cms import job_type
from core.log import logger
from core.menu import generate_menu, colsets, icons
from core.error import UserNotFound, EmptyQueueError, QueueInProgressException
from core.search import blog_search_results, site_search_results

from core.models import (Struct, get_site, get_blog, get_media, get_template,
    template_tags, get_page, Page, PageRevision, Blog, Queue, Template, Log,
    TemplateMapping, get_user, Plugin, Media, User, db, queue_jobs_waiting,
    MediaAssociation, Tag, template_type, publishing_mode, get_default_theme)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, response, redirect)
from core.libs import peewee

from settings import (BASE_URL, SECRET_KEY, _sep)

import re, datetime, json
from os.path import exists as _exists
from os import remove as _remove, makedirs

queue_selections = (
    ('Remove from queue', '1', ''),
    ('Change queue priority', '2', '')
    )

common_archive_mappings = (
    ('%Y/%m/{{blog.index_file}}', 'Yearly/monthly archive'),
    ('%Y/{{blog.index_file}}', 'Yearly archive'),
    ('{{page.user.name}}/{{blog.index_file}}', 'Author archive'),
    ('{{page.user.name}}/%Y/%m/{{blog.index_file}}', 'Author/yearly/monthly archive'),
    ('{{page.user.name}}/%Y/{{blog.index_file}}', 'Author/yearly archive'),
    ('{{page.primary_category.title}}/{{blog.index_file}}', 'Category archive'),
    ('{{page.primary_category.title}}/%Y/%m/{{blog.index_file}}', 'Category/yearly/monthly archive'),
    ('{{page.primary_category.title}}/%Y/{{blog.index_file}}', 'Category/yearly archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/{{blog.index_file}}', 'Category/author archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/%Y/%m/{{blog.index_file}}', 'Category/author/yearly/monthly archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/%Y/{{blog.index_file}}', 'Category/author/yearly archive'),
    )

common_page_mappings = (
    ('{{page.basename}}/{{blog.index_file}}', '{{page.basename}}/{{blog.index_file}}'),
    ('{{page.basename}}.{{blog.base_extension}}', '{{page.basename}}.{{blog.base_extension}}')
    )

common_index_mappings = (
    ('{{blog.index_file}}', 'Default index file type for blog'),
    )

template_mapping_index = {
    'Index':common_index_mappings,
    'Page':common_page_mappings,
    'Archive':common_archive_mappings,
    'Include':(),
    'Media':()
    }

search_context = (
    {'blog':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id),
            'form_description':'Search entries:',
            'form_placeholder':'Entry title, term in body text'},
    'blog_media':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/media",
            'form_description':'Search media:',
            'form_placeholder':'Media title, term in description, URL, etc.'},
    'blog_templates':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/templates",
            'form_description':'Search templates:',
            'form_placeholder':'Template title or text in template'},
    'site':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search blogs:',
            'form_placeholder':'Page title or text in description'},
    'sites':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search sites:',
            'form_placeholder':'Site title or text in description'},
    'blog_queue':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/queue",
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
    'site_queue':
            {'form_target':lambda x: BASE_URL + "/site/queue",  # @UnusedVariable
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
     'system_log':
            {'form_target':lambda x: BASE_URL + "/system/log",  # @UnusedVariable
            'form_description':'Search log:',
            'form_placeholder':'Log entry data, etc.'}
    }
    )

submission_fields = ('title', 'text', 'tag_text', 'excerpt')

status_badge = ('', 'warning', 'success', 'info')

save_action = (
    (None),
    (1, 'Save draft'),
    (3, 'Save & update live'),
    (1, 'Save draft')
    )

@transaction
def login():
    '''
    User login interface
    '''
    tpl = template('ui/ui_login',
        **template_tags().__dict__)

    logger.info("Login page requested from IP {}.".format(request.remote_addr))

    response.delete_cookie("login", path="/")

    return tpl

def login_verify():
    '''
    Verifies user login, provides session cookie if successful
    '''
    _forms = request.forms

    email = _forms.get('email')
    password = _forms.get('password')

    tags, success = login_verify_core(email, password)

    if success:
        if request.query.action:
            utils.safe_redirect(request.query.action)
        else:
            redirect(BASE_URL)

    else:
        return template('ui/ui_login',
            **tags.__dict__)

@transaction
def login_verify_core(email, password):

    try:
        user = mgmt.login_verify(email, password)
    except User.DoesNotExist:

        tags = template_tags()

        tags.status = utils.Status(
            type='danger',
            message="Email or password not found.")

        logger.info("User at {} attempted to log in as '{}'. User not found or password not valid.".format(
            request.remote_addr,
            email))

        return tags, False

    else:

        response.set_cookie("login", user.email, secret=SECRET_KEY, path="/")

        logger.info("User {} logged in from IP {}.".format(
            user.for_log,
            request.remote_addr))

        user.logout_nonce = utils.url_escape(utils.logout_nonce(user))
        user.save()

        return None, True


def logout():

    try:
        user = auth.is_logged_in_core(request)
    except UserNotFound:
        pass

    try:
        nonce = request.query['_']
    except KeyError:
        nonce = None

    if nonce == utils.url_unescape(user.logout_nonce):

        logger.info("User {} logged out from IP {}.".format(
            user.for_log,
            request.remote_addr))

        response.delete_cookie("login", path="/")

        redirect(BASE_URL)

    return "No logout nonce. <a href='{}/logout?_={}'>Click here to log out.</a>".format(
        BASE_URL, user.logout_nonce)

@transaction
def main_ui():
    '''
    Top level UI
    This will eventually become a full-blown user dashboard.
    Right now it just returns a list of sites in the system.
    All users for the system can see this dashboard.
    '''
    user = auth.is_logged_in(request)

    recent_pages = Page.select().where(
        Page.user == user).order_by(
        Page.modified_date.desc()).limit(10)

    your_blogs = user.blogs()

    tpl = template('ui/ui_dashboard',
        search_context=(search_context['sites'], None),
        menu=generate_menu('system', None),
        recent_pages=recent_pages,
        your_blogs=your_blogs,
        **template_tags(user=user).__dict__)

    return tpl

@transaction
def system_info():

    user = auth.is_logged_in(request)

    tags = template_tags(
        user=user)

    python_list = []
    environ_list = []
    settings_list = []

    # Generate interpreter info
    import os
    data = os.environ.__dict__['_data']
    for n in data:
        environ_list.append((n, data[n]))

    # List all settings variables
    import settings
    s_dict = settings.__dict__
    for n in s_dict:
        if n is not '__builtins__':
            settings_list.append((n, s_dict[n]))

    # List all plugins

    tpl = template('ui/ui_system_info',
        menu=generate_menu('all_sites', None),
        search_context=(search_context['sites'], None),
        environ_list=sorted(environ_list),
        settings_list=sorted(settings_list),
        **tags.__dict__)

    return tpl

@transaction
def system_sites(errormsg=None):

    user = auth.is_logged_in(request)

    try:
        sites_searched, search = site_search_results(request)
    except (KeyError, ValueError):
        sites_searched, search = None, None

    tags = template_tags(
        user=user)

    if errormsg is not None:
        tags.status = errormsg

    taglist = tags.sites

    paginator, rowset = utils.generate_paginator(taglist, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['sites'], None),
        menu=generate_menu('all_sites', None),
        rowset=rowset,
        colset=colsets['all_sites'],
        **tags.__dict__)

    return tpl


@transaction
def system_queue():

    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    queue = Queue.select().order_by(Queue.site.asc(), Queue.blog.asc(), Queue.job_type.asc(),
        Queue.date_touched.desc())

    tags = template_tags(user=user)

    paginator, queue_list = utils.generate_paginator(queue, request)

    tpl = template('queue/queue_ui',
        queue_list=queue_list,
        paginator=paginator,
        job_type=job_type.description,
        menu=generate_menu('system_queue', None),
        search_context=(search_context['site_queue'], None),
        **tags.__dict__)

    return tpl

@transaction
def system_log():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    log = Log.select().order_by(Log.date.desc(), Log.id.desc())

    tags = template_tags(user=user)
    paginator, rowset = utils.generate_paginator(log, request)

    tpl = template('listing/listing_ui',
        rowset=rowset,
        colset=colsets['system_log'],
        paginator=paginator,
        menu=generate_menu('system_log', None),
        search_context=(search_context['system_log'], None),
        **tags.__dict__)

    return tpl

@transaction
def system_plugins():

    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    tags = template_tags(
        user=user)

    plugins = Plugin.select()

    tpl = template('ui/ui_plugins',
        menu=generate_menu('system_plugins', None),
        search_context=(search_context['sites'], None),
        plugins=plugins,
        **tags.__dict__)

    return tpl

@transaction
def register_plugin(plugin_path):
    from core.plugins import register_plugin, PluginImportError
    try:
        new_plugin = register_plugin(plugin_path)
    except PluginImportError as e:
        return (str(e))
    return ("Plugin " + new_plugin.friendly_name + " registered.")



@transaction
def site(site_id, errormsg=None):
    '''
    UI for listing contents of a given site
    '''
    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_member(user, site)

    try:
        blogs_searched, search = site_search_results(request, site)
    except (KeyError, ValueError):
        blogs_searched, search = None, None

    # page = utils.page_list_id(request)

    tags = template_tags(site_id=site.id,
        search=search,
        user=user)

    if errormsg is not None:
        tags.status = errormsg

    taglist = tags.site.blogs

    paginator, rowset = utils.generate_paginator(taglist, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['site'], site),
        menu=generate_menu('site', site),
        rowset=rowset,
        colset=colsets['site'],
        icons=icons,
        **tags.__dict__)

    return tpl

@transaction
def site_create_user(site_id):
    '''
    Creates a user and gives it certain permissions within the context of a given blog
    '''

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)
    tags = template_tags(site_id=site.id,
        user=user)

    edit_user = Struct()
    edit_user.name = ""
    edit_user.email = ""

    tpl = template('edit/edit_user_settings',
        menu=generate_menu('site_create_users', site),
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        **tags.__dict__
        )

    return tpl

# TODO: add proper transaction support
def site_create_user_save(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    tags = template_tags(site_id=site.id,
        user=user)

    new_user = mgmt.create_user_site(
        name=request.forms.getunicode('user_name'),
        email=request.forms.getunicode('user_email')
        )

    redirect(BASE_URL + "/site/" + str(site.id) + "/user/" + str(new_user.id))

@transaction
def site_edit_user(site_id, user_id, status=None):

    user = auth.is_logged_in(request)

    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    edit_user = get_user(user_id=user_id)

    referer = request.headers.get('Referer')

    if (referer is None
        or edit_user.last_login is None
        or re.match(re.escape("/site/" + str(site.id) + "/users"), referer) is None):

        referer = BASE_URL + "/site/" + str(site.id) + "/users"

    if edit_user.last_login is None:

        status = utils.Status(
            type='success',
            message='User <b>{}</b> (#{}) successfully created.',
            vals=(edit_user.name, edit_user.id)
            )

        edit_user.last_login = datetime.datetime.now()
        edit_user.save()

    tags = template_tags(site_id=site.id,
        user=user,
        status=status)

    return site_edit_user_output(tags, edit_user)

@transaction
def site_edit_user_save(site_id, user_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    edit_user = get_user(user_id=user_id)

    # TODO: move to its own function?

    try:
        mgmt.update_user(edit_user, user,
            name=request.forms.getunicode('user_name'),
            email=request.forms.getunicode('user_email')
            )
    except peewee.IntegrityError:
        status = utils.Status(
            type='danger',
            message='Error: user <b>{}</b> (#{}) cannot be changed to the same name or email as another user.',
            vals=(edit_user.name, edit_user.id)
            )
    else:
        status = utils.Status(
            type='success',
            message='Data for user <b>{}</b> (#{}) successfully updated.',
            vals=(edit_user.name, edit_user.id)
            )

    tags = template_tags(site_id=site.id,
        user=user,
        status=status)

    return site_edit_user_output(tags, edit_user)

def site_edit_user_output(tags, edit_user):

    tpl = template('edit/edit_user_settings',
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        menu=generate_menu('site_manage_user', edit_user.from_site(tags.site)),
        **tags.__dict__
        )
    return tpl

@transaction
def site_list_users(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)
    user_list = site.users

    tags = template_tags(site_id=site.id,
        user=user)

    paginator, page_list = utils.generate_paginator(user_list, request)

    tpl = template('user_listing/listing_ui',
        menu=generate_menu('site_manage_users', site),
        search_context=(search_context['sites'], None),
        paginator=paginator,
        page_list=page_list,
        user_list=user_list,
        **tags.__dict__
        )

    return tpl

@transaction
def blog(blog_id, errormsg=None):
    '''
    UI for listing contents of a given blog
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    try:
        pages_searched, search = blog_search_results(request, blog)
    except (KeyError, ValueError):
        pages_searched, search = None, None

    tags = template_tags(blog_id=blog.id,
        search=search,
        user=user)

    taglist = tags.blog.pages(pages_searched)

    paginator, rowset = utils.generate_paginator(taglist, request)

    tags.status = errormsg if errormsg is not None else None

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog', blog),
        rowset=rowset,
        colset=colsets['blog'],
        icons=icons,
        **tags.__dict__)

    return tpl

@transaction
def blog_create(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    new_blog = Blog(
        name="",
        description="",
        url="",
        path="")

    tags = template_tags(site_id=site.id,
        user=user)

    tags.blog = new_blog

    tpl = template('ui/ui_blog_settings',
        section_title="Create new blog",
        search_context=(search_context['sites'], None),
        menu=generate_menu('create_blog', site),
        **tags.__dict__
        )

    return tpl

def blog_create_save(site_id):

    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_admin(user, site)

    new_blog = mgmt.blog_create(
        site=site,
        name=request.forms.getunicode('blog_name'),
        description=request.forms.getunicode('blog_description'),
        url=request.forms.getunicode('blog_url'),
        path=request.forms.getunicode('blog_path'),
        theme=get_default_theme(),
        )

    redirect(BASE_URL + "/blog/" + str(new_blog.id))

# TODO: make this universal to create a user for both a blog and a site
# use ka
@transaction
def blog_create_user(blog_id):
    '''
    Creates a user and gives it certain permissions within the context of a given blog
    '''

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    tags = template_tags(blog_id=blog.id,
        user=user)

    edit_user = Struct()
    edit_user.name = ""
    edit_user.email = ""

    tpl = template('edit/edit_user_settings',
        section_title="Create new blog user",
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        **tags.__dict__
        )

    return tpl



# TODO: make this universal to createa user for both a blog and a site
# use ka
# TODO: add proper transaction support
def blog_create_user_save(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    tags = template_tags(blog_id=blog.id,
        user=user)

    new_user = mgmt.create_user_blog(
        name=request.forms.getunicode('user_name'),
        email=request.forms.getunicode('user_email'),
        permission=127,
        blog=blog,
        site=blog.site
        )

    redirect(BASE_URL + "/blog/" + str(blog.id) + "/user/" + str(new_user.id))



# TODO: make this universal to createa user for both a blog and a site
# use ka
@transaction
def blog_user_edit(blog_id, user_id, status=None):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    edit_user = get_user(user_id=user_id)

    # TODO: add back in referer handler for new menus?
    referer = request.headers.get('Referer')

    if (referer is None
        or edit_user.last_login is None
        or re.match(re.escape("/blog/" + str(blog.id) + "/users"), referer) is None):

        referer = BASE_URL + "/blog/" + str(blog.id) + "/users"

    if edit_user.last_login is None:

        status = utils.Status(
            type='success',
            message='User <b>{}</b> (#{}) successfully created.',
            vals=(edit_user.name, edit_user.id)
            )

        edit_user.last_login = datetime.datetime.now()

        edit_user.save()

    tags = template_tags(blog_id=blog.id,
        user=user,
        status=status)

    return blog_user_edit_output(tags, edit_user)


# TODO: make this universal to createa user for both a blog and a site
# use ka
@transaction
def blog_user_edit_save(blog_id, user_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    edit_user = get_user(user_id=user_id)

    # TODO: move to its own function

    try:
        mgmt.update_user(edit_user,
            name=request.forms.getunicode('user_name'),
            email=request.forms.getunicode('user_email')
            )
    except peewee.IntegrityError:
        status = utils.Status(
            type='danger',
            message='Error: user <b>{}</b> (#{}) cannot be changed to the same name or email as another user.',
            vals=(edit_user.name, edit_user.id)
            # TODO: use standard form exception?
            )
    else:
        status = utils.Status(
            type='success',
            message='Data for user <b>{}</b> (#{}) successfully updated.',
            vals=(edit_user.name, edit_user.id)
            )

    tags = template_tags(blog_id=blog.id,
        user=user,
        status=status)

    return blog_user_edit_output(tags, edit_user)

def blog_user_edit_output(tags, edit_user):

    tpl = template('edit/edit_user_settings',
        section_title="Edit blog user #" + str(edit_user.id),
        search_context=(search_context['sites'], None),
        edit_user=edit_user,
        **tags.__dict__)

    return tpl

@transaction
def blog_list_users(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)
    user_list = blog.users

    tags = template_tags(blog_id=blog.id,
        user=user)

    paginator, page_list = utils.generate_paginator(user_list, request)

    tpl = template('user_listing/listing_ui',
        section_title="List blog users",
        search_context=(search_context['sites'], None),
        paginator=paginator,
        page_list=page_list,
        user_list=user_list,
        **tags.__dict__)

    return tpl



@transaction
def blog_new_page(blog_id):
    '''
    Displays UI for newly created (unsaved) page
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_author(user, blog)

    tags = template_tags(
        blog_id=blog.id,
        user=user)

    tags.page = Page()

    referer = request.headers.get('Referer')
    if referer is None:
        referer = BASE_URL + "/blog/" + str(blog.id)

    blog_new_page = tags.page

    for n in submission_fields:
        blog_new_page.__setattr__(n, "")
        if n in request.query:
            blog_new_page.__setattr__(n, request.query.getunicode(n))

    blog_new_page.blog = blog_id
    blog_new_page.user = user
    blog_new_page.publication_date = datetime.datetime.now()
    blog_new_page.basename = ''

    from core.cms import save_action_list

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(blog_new_page.kvs())

    tpl = template('edit/edit_page_ui',
        menu=generate_menu('create_page', blog),
        parent_path=referer,
        search_context=(search_context['blog'], blog),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui=kv_ui_data,
            **tags.__dict__),
        **tags.__dict__)

    return tpl

@transaction
def blog_new_page_save(blog_id):
    '''
    UI for saving a newly created page.
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    tags = cms.save_page(None, user, blog)

    # TODO: move to model instance?
    logger.info("Page {} created by user {}.".format(
        tags.page.for_log,
        user.for_log))

    response.add_header('X-Redirect', BASE_URL + '/page/{}/edit'.format(str(tags.page.id)))

    return response

@transaction
def blog_media(blog_id):
    '''
    UI for listing media for a given blog
    '''

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_member(user, blog)

    media = blog.media.order_by(Media.id.desc())

    tags = template_tags(blog_id=blog.id,
        user=user)

    paginator, media_list = utils.generate_paginator(media, request)
    # media_list = media.paginate(paginator['page_num'], ITEMS_PER_PAGE)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        media_list=media_list,
        menu=generate_menu('blog_manage_media', blog),
        icons=icons,
        search_context=(search_context['blog_media'], blog),
        rowset=media_list,
        colset=colsets['media'],
        **tags.__dict__)

    return tpl

@transaction
def blog_media_edit(blog_id, media_id, status=None):
    '''
    UI for editing a given media entry
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id, blog)
    permission = auth.is_media_owner(user, media)

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user)

    return blog_media_edit_output(tags)

@transaction
def blog_media_edit_save(blog_id, media_id):
    '''
    Save changes to a media entry.
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id)
    permission = auth.is_media_owner(user, media)

    friendly_name = request.forms.getunicode('media_friendly_name')

    changes = False

    if friendly_name != media.friendly_name:
        changes = True
        media.friendly_name = friendly_name

    if changes is True:
        media.modified_date = datetime.datetime.now()
        media.save()

        status = utils.Status(
            type='success',
            message='Changes to media <b>#{} ({})</b> have been saved.',
            vals=(media.id, media.friendly_name)
            )
    else:

        status = utils.Status(
            type='warning',
            message='No discernible changes submitted for media <b>#{} ({})</b>.',
            vals=(media.id, media.friendly_name)
            )

    logger.info("Media {} edited by user {}.".format(
        media.for_log,
        user.for_log))

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user)

    return blog_media_edit_output(tags)

def blog_media_edit_output(tags):

    tpl = template('edit/edit_media_ui',
        icons=icons,
        menu=generate_menu('blog_edit_media', tags.media),
        search_context=(search_context['blog_media'], tags.blog),
        **tags.__dict__)

    return tpl

# TODO: be able to process multiple media at once via a list
# using the list framework
# also allows for actions like de-associate, etc.
# any delete action that works with an attached asset, like a tag, should also behave this way
@transaction
def blog_media_delete(blog_id, media_id, confirm='N'):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id, blog)
    permission = auth.is_media_owner(user, media)

    tags = template_tags(blog_id=blog.id,
        user=user)

    report = []

    if confirm == "y":

        try:
            _remove(media.path)
        except:
            pass

        media.delete_instance(recursive=True,
            delete_nullable=True)

        report.append('<h3>Media <b>#{} ({})</b> successfully deleted</h3>'.format(
            media.id, media.friendly_name))
        report.append('<a href="{}/blog/{}/media">Return to the media listing</a>'.format(
            BASE_URL, blog.id))
    else:
        report.append('<h3>You are about to delete media object <a href="{}">{}</a> from blog <b>{}</b></h3>'.format(
            media.link_format,
            media.for_display,
            blog.for_display))
        report.append("If you delete this media object, it will no longer be available to the following pages:")

        used_in_tpl = "<ul>{}</ul>"
        used_in = []

        for n in media.associated_with:
            used_in.append("<li>{}</li>".format(n.page.for_display))

        report.append(used_in_tpl.format("".join(used_in)))

        ok_button = '''
<hr/>
<form method='post'>{}<input type='hidden' name='confirm' value='y'>
<span class="pull-right">
<a href="../{}/edit"><button type='button' class='btn btn-primary'>No, cancel</button></a>
</span>
<button class='btn btn-danger' action='submit'>Yes, delete this media</button>
</form>
'''.format(tags.csrf_token, media.id)

        report.append(ok_button)



    tpl = template('listing/report',
        menu=generate_menu('blog_delete_media', media),
        icons=icons,
        report=report,
        search_context=(search_context['blog_media'], blog),
        **tags.__dict__)

    return tpl

@transaction
def blog_tags(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_author(user, blog)

    reason = auth.check_tag_editing_lock(blog, True)

    blog_tag_list = Tag.select().where(
        Tag.blog == blog).order_by(Tag.tag.asc())

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.status = reason

    paginator, rowset = utils.generate_paginator(blog_tag_list, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_manage_tags', blog),
        rowset=rowset,
        colset=colsets['tags'],
        icons=icons,
        **tags.__dict__)

    return tpl

@transaction
def blog_templates(blog_id):
    '''
    List all templates in a given blog
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_designer(user, blog)

    reason = auth.check_template_lock(blog, True)

    tags = template_tags(blog_id=blog.id,
        user=user)

    tags.status = reason

    template_list = Template.select(Template, TemplateMapping).join(
        TemplateMapping).where(
        # (TemplateMapping.is_default == True) &
        (Template.blog == blog)
        ).order_by(Template.title)

    index_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.index)

    page_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.page)

    archive_templates = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.archive)

    template_includes = template_list.select(Template, TemplateMapping).where(
        Template.template_type == template_type.include)


    tags.list_items = [
        {'title':'Index Templates',
        'type': template_type.index,
        'data':index_templates},
        {'title':'Page Templates',
        'type': template_type.page,
        'data':page_templates},
        {'title':'Archive Templates',
        'type': template_type.archive,
        'data':archive_templates},
        {'title':'Includes',
        'type': template_type.include,
        'data':template_includes},
        ]

    tpl = template('ui/ui_blog_templates',
        icons=icons,
        section_title="Templates",
        publishing_mode=publishing_mode,
        search_context=(search_context['blog_templates'], blog),
        menu=generate_menu('blog_manage_templates', blog),
        ** tags.__dict__)

    return tpl

@transaction
def blog_republish(blog_id):
    '''
    UI for republishing an entire blog
    Eventually to be reworked
    '''
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    report = cms.republish_blog(blog_id)

    tpl = template('listing/report',
        report=report,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_republish', blog),
        **template_tags(blog_id=blog.id,
            user=user).__dict__)

    return tpl

@transaction
def blog_purge(blog_id):
    '''
    UI for purging/republishing an entire blog
    Eventually to be reworked
    '''

    user = auth.is_logged_in(request)

    blog = get_blog(blog_id)

    permission = auth.is_blog_publisher(user, blog)

    report = cms.purge_blog(blog)

    tpl = template('listing/report',
        report=report,
        search_context=(search_context['blog'], blog),
        menu=generate_menu('blog_purge', blog),
        **template_tags(blog_id=blog.id,
            user=user).__dict__)

    return tpl

@transaction
def blog_queue(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    '''
    queue = Queue.select().where(Queue.blog == blog_id).order_by(Queue.site.asc(), Queue.blog.asc(),
        Queue.job_type.asc(),
        Queue.date_touched.desc())
    '''
    # queue = queue_jobs_waiting(blog=blog)

    tags = template_tags(blog_id=blog.id,
            user=user)

    paginator, queue_list = utils.generate_paginator(tags.queue, request)

    tpl = template('queue/queue_ui',
        queue_list=queue_list,
        paginator=paginator,
        job_type=job_type.description,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_queue', blog),
        **tags.__dict__)

    return tpl


@transaction
def blog_settings(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    auth.check_settings_lock(blog)

    tags = template_tags(blog_id=blog.id,
        user=user)

    return blog_settings_output(tags)

@transaction
def blog_settings_save(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    status = mgmt.blog_settings_save(request, blog, user)

    tags = template_tags(blog_id=blog.id,
        user=user)

    if status is not None:
        tags.status = status

    return blog_settings_output(tags)

def blog_settings_output(tags):

    tpl = template('ui/ui_blog_settings',
        section_title='Basic settings',
        search_context=(search_context['blog'], tags.blog),
        menu=generate_menu('blog_settings', tags.blog),
        **tags.__dict__)

    return tpl


@transaction
def blog_publish(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    # TODO: check if control job already exists, if so, report back and quit

    '''
    queue = Queue.select().where(
        Queue.blog == blog.id,
        Queue.is_control == False)

    queue_length = queue.count()
    '''
    queue = Queue.select().where(
        Queue.blog == blog.id)

    queue_length = queue_jobs_waiting(blog=blog)

    tags = template_tags(blog_id=blog.id,
            user=user)

    if queue_length > 0:

        start_message = template('queue/queue_run_include',
            queue=queue,
            percentage_complete=0)

        try:
            Queue.get(Queue.site == blog.site,
                Queue.blog == blog,
                Queue.is_control == True)

        except Queue.DoesNotExist:

            cms.push_to_queue(blog=blog,
                site=blog.site,
                job_type=job_type.control,
                is_control=True,
                data_integer=queue_length
                )
    else:

        start_message = "Queue empty."

    tpl = template('queue/queue_run_ui',
        original_queue_length=queue_length,
        start_message=start_message,
        search_context=(search_context['blog_queue'], blog),
        menu=generate_menu('blog_queue', blog),
        **tags.__dict__)

    return tpl

@transaction
def blog_publish_progress(blog_id, original_queue_length):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    try:
        queue_count = cms.process_queue(blog)
    except EmptyQueueError:
        queue_count = 0
    except BaseException as e:
        raise e

    percentage_complete = int((1 - (int(queue_count) / int(original_queue_length))) * 100)

    tpl = template('queue/queue_run_include',
            queue_count=queue_count,
            percentage_complete=percentage_complete)

    return tpl

@transaction
def blog_publish_process(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    # queue_jobs_waiting should report actual JOBS
    # queue_control_jobs_waiting should report CONTROL JOBS
    # both should return a tuple of the actual queue and the queue count

    # get how many control jobs we have
    queue = Queue.select().where(Queue.blog == blog.id,
                Queue.is_control == True)

    queue_count = queue.count()
    if queue_count == 0:

        # get how many regular jobs we have
        queue = Queue.select().where(Queue.blog == blog_id,
                Queue.is_control == False)

        if queue.count() > 0:

            cms.push_to_queue(blog=blog,
                site=blog.site,
                job_type=job_type.control,
                is_control=True,
                data_integer=queue.count()
                )


            queue_count = cms.process_queue(blog)

    else:
        queue_count = cms.process_queue(blog)

    tpl = template('queue/queue_counter_include',
            queue_count=queue_count)

    return tpl


def new_template(blog_id, template_type):
    with db.atomic() as txn:

        user = auth.is_logged_in(request)
        blog = get_blog(blog_id)
        permission = auth.is_blog_designer(user, blog)

        auth.check_template_lock(blog)

        mappings_index = template_mapping_index.get(template_type, None)
        if mappings_index is None:
            raise Exception('Mapping type not found')

        template = Template(
            blog=blog,
            theme=blog.theme,
            template_type=template_type,
            publishing_mode=publishing_mode.do_not_publish,
            body='',
            )
        template.save()
        template.title = 'Untitled Template #{}'.format(template.id)
        template.save()

        new_template_mapping = TemplateMapping(
           template=template,
           # archive_type=1,
           is_default=True,
           path_string=utils.create_basename(template.title, blog)
           )

        new_template_mapping.save()


    redirect(BASE_URL + '/template/{}/edit'.format(
        template.id))

@transaction
def template_edit(template_id):
    '''
    UI for editing a blog template
    '''

    user = auth.is_logged_in(request)
    edit_template = get_template(template_id)
    blog = get_blog(edit_template.blog.id)
    permission = auth.is_blog_designer(user, blog)

    auth.check_template_lock(blog)

    utils.disable_protection()

    tags = template_tags(template_id=template_id,
                        user=user)

    # find out if the template object returns a list of all the mappings, or just the first one
    # it's edit_template.mappings

    tags.mappings = template_mapping_index[edit_template.template_type]

    return template_edit_output(tags)

def template_delete(template):
    _template.delete(template)
    return "Deleted"

@transaction
def template_edit_save(template_id):
    '''
    UI for saving a blog template
    '''
    user = auth.is_logged_in(request)
    template = get_template(template_id)
    blog = get_blog(template.blog)
    permission = auth.is_blog_designer(user, blog)

    from core.utils import Status
    from core.error import TemplateSaveException

    status = None

    save_mode = int(request.forms.getunicode('save', default="0"))

    if save_mode == 4:
        if request.forms.getunicode('confirm') == 'Y':
            return template_delete(template)
        else:
            status = Status(
                type='warning',
                message='You are attempting to delete this template. Are you sure you want to do this?',
                confirm=('save', '4')
                )

    if save_mode in (1, 2):
        try:
            message = _template.save(request, user, template)
        except TemplateSaveException as e:
            status = Status(
                type='danger',
                message="Error saving template <b>{}</b>: <br>{}",
                vals=(template.for_log,
                    e)
                )
        except BaseException as e:
            status = Status(
                type='warning',
                message="Problem saving template <b>{}</b>: <br>{}",
                vals=(template.for_log,
                    e)
                )
        else:
            status = Status(
                type='success',
                message="Template <b>{}</b> saved.{}",
                vals=(template.for_log, message)
                )

    tags = template_tags(template_id=template_id,
                        user=user)

    tags.mappings = template_mapping_index[template.template_type]

    tags.status = status

    return template_edit_output(tags)

def template_preview(template_id):

    template = get_template(template_id)

    if template.template_type == template_type.index:
        tags = template_tags(blog=template.blog)
    if template.template_type == template_type.page:
        tags = template_tags(page=template.blog.published_pages()[0])

    tpl_output = utils.tpl(template.body,
        **tags.__dict__)

    return tpl_output

def template_edit_output(tags):

    from core.models import (publishing_mode,
        template_type as template_types)

    tpl = template('edit/edit_template_ui',
        icons=icons,
        search_context=(search_context['blog'], tags.blog),
        menu=generate_menu('blog_edit_template', tags.template),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_template',
            publishing_mode=publishing_mode,
            types=template_types,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl


page_edit_functions = {
    'append': lambda x, y:x + y,
    'prepend':lambda x, y:y + x
    }

media_buttons = '''
<button type="button" id="modal_close_button" class="btn btn-default" data-dismiss="modal">Close</button>
<button type="button" {} class="btn btn-primary">{}</button>
'''


@transaction
# TODO: page-locking algorithm
def page_edit(page_id):
    '''
    UI for editing a page in a blog
    '''
    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    from core.cms import save_action_list

    status = None
    referer = request.headers.get('Referer')

    if (referer is None
        or page.modified_date is None
        or re.match(re.escape(BASE_URL + "/blog/" + str(page.blog.id)), referer) is None):

        referer = BASE_URL + "/blog/" + str(page.blog.id)

    if page.modified_date is None:
        status = utils.Status(
            type='info',
            message="Page <b>{}</b> created.",
            vals=(page.title,))
        page.modified_date = datetime.datetime.now()
        page.save(user)

    tags = template_tags(page_id=page_id,
        user=user,
        status=status)

    for n in request.query:
        try:
            tags.page.text = page_edit_functions[n](tags.page.text, request.query[n])
        except KeyError: pass

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(page.kvs())

    tpl = template('edit/edit_page_ui',
        menu=generate_menu('edit_page', page),
        parent_path=referer,
        search_context=(search_context['blog'], page.blog),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action_list=save_action_list,
            save_action=save_action,
            kv_ui=kv_ui_data,
            **tags.__dict__),
        **tags.__dict__)

    logger.info("Page {} opened for editing by {}.".format(
        page.for_log,
        user.for_log))



    return tpl

@transaction
def page_edit_save(page_id):
    '''
    UI for saving changes to an edited blog page
    '''

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    tags = cms.save_page(page, user, page.blog)

    from core.cms import save_action_list

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(page.kvs())

    tpl = template('edit/edit_page_ajax_response',
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui=kv_ui_data,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl

@transaction
def page_delete(page_id):
    '''
    Deletes a selected page -- no confirmation yet
    Returns user to list of pages in blog with a notice about the deleted file
    '''

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    blog_id = page.blog.id

    delete_query = page.delete_instance(
        recursive=True,
        delete_nullable=True)

    status = utils.Status(
        type='success',
        message='Page <b>{}</b> (#{}) has been deleted from the database.',
        vals=(page.title, page.id)
        )

    logger.info("Page {} deleted by user {}.".format(
        page_id,
        user.for_log))

    # TODO: proper delete page, not a repurposing of the main page
    return ("Deleted.")

@transaction
def page_preview(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    f = page.default_fileinfo
    tags = template_tags(page=page)
    page_text = cms.generate_page_text(f, tags)

    utils.disable_protection()

    return page_text

@transaction
def page_public_preview(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    # generate the page text
    # write it to the preview URL, same as the page w/"_preview" prepended to it
    # check to make sure that preview URL has no name collisions
    # return a redirect to the successfully-written URL


@transaction
def page_revisions(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    tags = template_tags(page_id=page_id)

    try:
        tpl = template('modal/modal_revisions',
        title='Revisions for page #{}'.format(page.id),
        buttons='',
        **tags.__dict__)
    except:
        raise

    return tpl

@transaction
def page_media_upload_confirm(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    # get file NAMES, attributes, size, etc. first
    # request.form.getunicode('filename')
    # check each one on the SERVER side, not the client
    # if each file is OK, then respond appropriately and have the client send the whole file
    # if not, respond with a warning to be added to the notification area

    _g = request.forms.getunicode

    file_name = _g('filename')
    file_size = _g('filesize')

    # check for file types against master list
    # check for file length
    # check for name collision

    for n in request.files:
        x = request.files.get(n)
        file_path = page.blog.local_path + page.blog.media_path + _sep + x.filename
        if _exists(file_path):
            pass
        else:
            pass

@transaction
def page_media_upload(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    overwrite = []

    for n in request.files:
        x = request.files.get(n)
        media_path = page.blog.local_path + page.blog.media_path
        file_path = media_path + _sep + x.filename
        if _exists(file_path):
            from core.error import FileExistsError
            raise FileExistsError("File '{}' already exists on the server.".format(
                utils.html_escape(x.filename)))
        else:
            # with db.atomic():
            cms.register_media(x.filename, file_path, user, page=page)
            if not _exists(media_path):
                makedirs(media_path)
            x.save(file_path)

    tags = template_tags(page_id=page_id)

    return template('edit/edit_page_sidebar_media_list.tpl',
        **tags.__dict__)

@transaction
def page_media_delete(page_id, media_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    media = get_media(media_id)
    media_reference = MediaAssociation.get(
        MediaAssociation.page == page,
        MediaAssociation.media == media)
    media_reference.delete_instance(recursive=True,
        delete_nullable=True)

    tags = template_tags(page_id=page_id)

    return template('edit/edit_page_sidebar_media_list.tpl',
        **tags.__dict__)


def page_get_media_templates(page_id, media_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    media = get_media(media_id, page.blog)

    media_templates = Template.select().where(
        Template.blog == page.blog,
        Template.template_type == template_type.media)

    buttons = media_buttons.format(
        'onclick="add_template();"',
        'Apply')

    tpl = template('modal/modal_image_templates',
        media=media,
        templates=media_templates,
        buttons=buttons,
        title='Choose a template for {}'.format(
            media.for_log))

    return tpl

def page_add_media_with_template(page_id, media_id, template_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    media = get_media(media_id, page.blog)

    media_template = Template.get(
        Template.id == template_id)

    generated_template = utils.tpl(media_template.body,
        media=media)

    return generated_template

@transaction
def page_revision_restore(page_id, revision_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    page_revision = PageRevision.select().where(PageRevision.id == revision_id).get()

    status = utils.Status(
        type='success',
        message='Page <b>{}</b> (#{}) has been restored from backup dated {}.',
        vals=(page.title, page.id, page_revision.modified_date)
        )

    tags = template_tags(page_id=page_id,
        user=user,
        status=status)

    page_revision.id = page.id
    tags.page = page_revision

    referer = BASE_URL + "/blog/" + str(page.blog.id)

    from core.cms import save_action_list

    tpl = template('edit/edit_page_ui',
        status_badge=status_badge,
        save_action=save_action,
        menu=generate_menu('edit_page', page),
        search_context=(search_context['blog'], page.blog),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl

@transaction
def page_revision_restore_save(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    tags = cms.save_page(page, user, page.blog)

    from core.cms import save_action_list

    tpl = template('edit/edit_page_ajax_response',
        status_badge=status_badge,
        save_action=save_action,
        save_action_list=save_action_list,
        sidebar='',
        **tags.__dict__)

    response.add_header('X-Redirect', BASE_URL + '/page/{}/edit'.format(str(tags.page.id)))

    return tpl

@transaction
def edit_tag(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_editor(user, blog)

    auth.check_tag_editing_lock(blog)

    try:
        tag = Tag.get(Tag.id == tag_id)
    except Tag.DoesNotExist:
        raise Tag.DoesNotExist("No such tag #{} in blog {}.".format(
            tag_id,
            blog.for_log))

    if request.method == "POST":
        pass
        # change tag
        # get list of all assets with changed tag
        # provide link
        # need to build search by tag ID

    tags = template_tags(
        user=user)

    tpl = template('edit/edit_tag_ui',
        menu=generate_menu('edit_tag', tag),
        search_context=(search_context['sites'], None),
        tag=tag,
        **tags.__dict__)

    return tpl

@transaction
def get_tag(tag_name):

    tag_list = Tag.select().where(
        Tag.tag.contains(tag_name))

    try:
        blog = request.query['blog']
    except KeyError:
        blog = None

    if blog:
        tag_list = tag_list.select().where(Tag.blog == blog)

    tag_list_json = json.dumps([{'tag':t.tag,
                                'id':t.id} for t in tag_list])

    return tag_list_json

@transaction
def make_tag_for_page(blog_id=None, page_id=None):

    user = auth.is_logged_in(request)

    if page_id is None:
        page = Page()
        blog = get_blog(blog_id)
        permission = auth.is_blog_editor(user, blog)
    else:
        page = get_page(page_id)
        blog = page.blog
        permission = auth.is_page_editor(user, page)

    tag_name = request.forms.getunicode('tag')

    if len(tag_name) < 1:
        return None

    try:
        tag = Tag.get(Tag.tag == tag_name,
            Tag.blog == blog)
    except Tag.DoesNotExist:
        new_tag = Tag(tag=tag_name,
            blog=blog)
        tpl = template(new_tag.new_tag_for_display)

    else:
        tpl = template(tag.for_display)

    return tpl


