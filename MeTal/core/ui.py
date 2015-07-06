from core import (auth, mgmt, utils, cms, ui_mgr)
from core.cms import job_type
from core.log import logger
from core.menu import generate_menu, colsets, icons
from core.error import UserNotFound, EmptyQueueError
from core.search import blog_search_results, site_search_results

from models import (Struct, get_site, get_blog, get_media, get_template,
    template_tags, get_page, Page, PageRevision, Blog, Queue, Template, Log,
    TemplateMapping, get_user, Plugin, Media, User, db,
    MediaAssociation, Tag, template_type)

from models.transaction import transaction

from libs.bottle import (template, request, response, redirect)
from libs import peewee

from settings import (BASE_URL, BASE_PATH, SECRET_KEY, _sep)

import re, datetime, json
from os.path import exists as _exists
from os import remove as _remove

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
    tpl = template('login_ui',
        **template_tags().__dict__)

    logger.info("Login page requested from IP {}.".format(request.remote_addr))
    
    response.add_header('X-Content-Security-Policy', "allow 'self'")
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
        return template('login_ui',
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
        response.add_header('X-Content-Security-Policy', "allow 'self'")
        
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
    
    tpl = template('main_ui',
        search_context=(search_context['sites'], None),
        menu=generate_menu('system', None),
        recent_pages=recent_pages,
        your_blogs=your_blogs,
        **template_tags(user=user).__dict__)

    return tpl

@transaction
def system_sites(errormsg=None):
        
    user = auth.is_logged_in(request)
    # permission = auth.is_sys_admin(user)
    
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
    
    tpl = template('listing_ui',
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
            
    tpl = template('queue_ui',
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
            
    tpl = template('listing_ui',
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
    
    tpl = template('plugins_ui',
        menu=generate_menu('system_plugins', None),
        search_context=(search_context['sites'], None),
        plugins=plugins,
        **tags.__dict__)
    
    return tpl

@transaction
def register_plugin(plugin_path):
    from data.plugins import register_plugin, PluginImportError
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
        blogs_searched, search = site_search_results(request, site.id)
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
    
    tpl = template('listing_ui',
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
    
    tpl = template('user_settings_ui',
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
    
    tpl = template('user_settings_ui',
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
            
    tpl = template('user_listing_ui',
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
    
    tpl = template('listing_ui',
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
    
    tpl = template('blog_settings_ui',
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
    
    new_blog = mgmt.create_blog(
        site=site,
        name=request.forms.getunicode('blog_name'),
        description=request.forms.getunicode('blog_description'),
        url=request.forms.getunicode('blog_url'),
        path=request.forms.getunicode('blog_path'),
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
    
    tpl = template('user_settings_ui',
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
    
    tpl = template('user_settings_ui',
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
            
    tpl = template('user_listing_ui',
        section_title="List blog users",
        search_context=(search_context['sites'], None),
        paginator=paginator,
        page_list=page_list,
        user_list=user_list,
        **tags.__dict__
        )
    
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
    
    tpl = template('edit_page_ui',
        menu=generate_menu('create_page', blog),
        parent_path=referer,
        search_context=(search_context['blog'], blog),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            **tags.__dict__
            ),
        **tags.__dict__
    )

    response.add_header('X-Content-Security-Policy', "allow 'self'")    

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
        
    response.add_header('X-Content-Security-Policy', "allow 'self'")
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
    
    tpl = template('listing_ui',
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
    
    tpl = template('edit_media_ui',
        icons=icons,
        menu=generate_menu('blog_edit_media', tags.media),
        search_context=(search_context['blog_media'], tags.blog),
        **tags.__dict__)
        
    response.add_header('X-Content-Security-Policy', "allow 'self'")
    return tpl

# TODO: make this into its own url, /delete
# with a list of all the pages that will be affected by this delete action
# maybe later also offer the option to cleanly remove links to such things?
@transaction
def blog_media_delete(blog_id, media_id):
    
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = get_media(media_id, blog)
    permission = auth.is_media_owner(user, media)
    
    tags = template_tags(blog_id=blog.id,
        user=user)
    
    report = []
        
    if request.forms.get('confirm') == "y":
        
        try:
            _remove(media.path)
        except BaseException:
            raise
        
        media.delete_instance(recursive=True,
            delete_nullable=True)
    
        report.append('<h3>Media <b>#{} ({})</b> successfully deleted</h3>'.format(
            media.id, media.friendly_name))
        report.append('<a href="{}/blog/{}/media">Return to the media listing</a>'.format(
            BASE_PATH, blog.id))
    else:
        report.append('<h3>You are about to delete media object <b>#{} ({})</b> from blog <b>{}</b></h3>'.format(
            media.id, media.friendly_name,
            blog.for_display))
        report.append("If you delete this media object, it will no longer be available to the following pages:")
        
        used_in_tpl = "<ul>{}</ul>"
        used_in = []
        
        for n in media.associated_with:
            used_in.append("<li>{}</li>".format(n.page.for_display))
            
        report.append(used_in_tpl.format("".join(used_in)))
        
        ok_button = '''
<form method='post'>{}<input type='hidden' name='confirm' value='y'>
<button class='btn' action='submit'>Delete</button></form>
'''.format(tags.csrf_token)
        
        report.append(ok_button)       
    
    
    
    tpl = template('report_ui',
        menu=generate_menu('blog_manage_media', blog),
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
    
    blog_tag_list = Tag.select().where(
        Tag.blog == blog).order_by(Tag.tag.asc())
    
    tags = template_tags(blog_id=blog.id,
        user=user)

    paginator, rowset = utils.generate_paginator(blog_tag_list, request)
    
    tpl = template('listing_ui',
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
    from models import publishing_mode
    
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_designer(user, blog)

    tags = template_tags(blog_id=blog.id,
        user=user)
    
    template_list = Template.select(Template, TemplateMapping).join(
        TemplateMapping).where(
        (TemplateMapping.is_default == True) & 
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
        'data':index_templates},
        {'title':'Page Templates',
        'data':page_templates},
        {'title':'Archive Templates',
        'data':archive_templates},
        {'title':'Includes',
        'data':template_includes},
        ]

    tpl = template('blog_templates_ui',
        icons=icons,
        section_title="Templates",
        publishing_mode=publishing_mode,
        search_context=(search_context['blog_templates'], blog),
        menu=generate_menu('blog_manage_templates', blog),
        **tags.__dict__)

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

    tpl = template('report_ui',
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

    tpl = template('report_ui',
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
        
    queue = Queue.select().where(Queue.blog == blog_id).order_by(Queue.site.asc(), Queue.blog.asc(),
        Queue.job_type.asc(),
        Queue.date_touched.desc())
    
    tags = template_tags(blog_id=blog.id,
            user=user)
    
    paginator, queue_list = utils.generate_paginator(queue, request)    
            
    tpl = template('queue_ui',
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
    
    tpl = template('blog_settings_ui',
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
    
    queue = Queue.select().where(
        Queue.blog == blog.id,
        Queue.is_control == False)
    
    queue_length = queue.count()    
    
    tags = template_tags(blog_id=blog.id,
            user=user)
    
    if queue_length > 0:
        
        start_message = template('queue_run_include',
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
            
    tpl = template('queue_run_ui',
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
    
    tpl = template('queue_run_include',
            queue_count=queue_count,
            percentage_complete=percentage_complete)
    
    return tpl

@transaction
def blog_publish_process(blog_id):

    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_publisher(user, blog)
    
    queue = Queue.select().where(Queue.blog == blog.id,
                Queue.is_control == True)

    if queue.count() == 0:
        
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

    tpl = template('queue_counter_include',
            queue_count=queue_count)
        
    return tpl


@transaction
def template_edit(template_id):
    '''
    UI for editing a blog template
    '''

    user = auth.is_logged_in(request)
    edit_template = get_template(template_id)
    blog = get_blog(edit_template.blog.id)
    permission = auth.is_blog_designer(user, blog)
    
    tags = template_tags(template_id=template_id,
                        user=user)

    tags.mappings = template_mapping_index[edit_template.template_type]
    
    return template_edit_output(tags)

@transaction
def template_edit_save(template_id):
    '''
    UI for saving a blog template
    '''
    user = auth.is_logged_in(request)
    template = get_template(template_id)
    blog = get_blog(template.blog)
    permission = auth.is_blog_designer(user, blog)
    status = mgmt.save_template(request, user, template)
    
    tags = template_tags(template_id=template_id,
                        user=user)
    
    tags.mappings = template_mapping_index[template.template_type]
    
    if status is not None:
        tags.status = status
    
    return template_edit_output(tags)
    

def template_edit_output(tags):
    
    tpl = template('edit_template_ui',
        icons=icons,
        search_context=(search_context['blog'], tags.blog),
        menu=generate_menu('blog_edit_template', tags.template),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_template',
            **tags.__dict__
            ),
        **tags.__dict__)

    response.add_header('X-Content-Security-Policy', "allow 'self'")
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
   
    tpl = template('edit_page_ui',
        menu=generate_menu('edit_page', page),
        parent_path=referer,
        search_context=(search_context['blog'], page.blog),
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action_list=save_action_list,
            save_action=save_action,
            kv_ui = kv_ui_data,
            **tags.__dict__),
        **tags.__dict__)

    response.add_header('X-Content-Security-Policy', "allow 'self'")
    
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
        
    tpl = template('edit_page_ajax_response',
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui = kv_ui_data,
            **tags.__dict__
            ),
        **tags.__dict__)

    response.add_header('X-Content-Security-Policy', "allow 'self'")

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
    
    # TODO: move to model?
    logger.info("Page {} deleted by user {}.".format(
        page_id,
        user.for_log))

    # TODO: proper delete page, not a repurposing of the main page
    return ("Deleted.")

@transaction
def page_preview(page_id):
    
    with db.atomic():
        user = auth.is_logged_in(request)
        page = get_page(page_id)
        permission = auth.is_page_editor(user, page)
        
    f = page.fileinfos[0]
    tags = template_tags(page_id=f.page.id)
    page_text = cms.generate_page_text(f, tags)
        
    return page_text

@transaction
def page_revisions(page_id):
    
    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    tags = template_tags(page_id=page_id)
    
    tpl = template('revisions_modal',
        **tags.__dict__)
    
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
        file_path = page.blog.local_path + page.blog.media_path + _sep + x.filename
        if _exists(file_path):
            raise FileExistsError("File '{}' already exists on the server.".format(
                utils.html_escape(x.filename)))
        else:
            cms.register_media(x.filename, file_path, user, page=page)
            x.save(file_path)
            
            
    tags = template_tags(page_id=page_id)
    
    return template('edit_page_sidebar_media_list.tpl',
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
    
    return template('edit_page_sidebar_media_list.tpl',
        **tags.__dict__)
            

def page_get_media_templates(page_id, media_id):
    
    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    
    media = get_media(media_id, page.blog)
    
    media_templates = Template.select().where(
        Template.blog == page.blog,
        Template.template_type == template_type.media)
    
    media_tpl = template('image_templates',
        media=media,
        templates=media_templates)
    
    buttons = media_buttons.format(
        'onclick="add_template();"',
        'Apply')
    
    tpl = template('modal',
        base=media_tpl,
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
    
    tpl = template('edit_page_ui',
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
    
    response.add_header('X-Content-Security-Policy', "allow 'self'")
    
    return tpl

@transaction
def page_revision_restore_save(page_id):
    
    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)
    tags = cms.save_page(page, user, page.blog)
    
    from core.cms import save_action_list
    
    tpl = template('edit_page_ajax_response',
        status_badge=status_badge,
        save_action=save_action,
        save_action_list=save_action_list,
        sidebar='',
        **tags.__dict__)

    response.add_header('X-Content-Security-Policy', "allow 'self'")
    response.add_header('X-Redirect', BASE_URL + '/page/{}/edit'.format(str(tags.page.id)))
    
    return tpl

@transaction
def edit_tag(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_editor(user, blog)
    
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
    
    tpl = template('edit_tag_ui',
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


