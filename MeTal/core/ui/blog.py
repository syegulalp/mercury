from core import (auth, mgmt, utils, cms, ui_mgr)
from core.cms import job_type
from core.log import logger
from core.menu import generate_menu, colsets, icons
from core.error import EmptyQueueError
from core.search import blog_search_results
from .ui import search_context, submission_fields, status_badge, save_action

from core.models import (Struct, get_site, get_blog, get_media,
    template_tags, Page, Blog, Queue, Template,
    TemplateMapping, get_user, Media, db, queue_jobs_waiting,
    Tag, template_type, publishing_mode, get_default_theme)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, response, redirect)
from core.libs import peewee

from settings import (BASE_URL)

import re, datetime
from os import remove as _remove


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

    with db.atomic():
        user = auth.is_logged_in(request)
        site = get_site(site_id)
        permission = auth.is_site_admin(user, site)

        # return (get_default_theme().json)

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
            message='Changes to media <b>#{} ({})</b> saved successfully.',
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