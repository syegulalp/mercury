from core import (auth, utils, cms)
from core.ui import sidebar
from core.log import logger
from core.menu import generate_menu
from . import search_context, status_badge, save_action

from core.models import (Media,
    template_tags, Page, PageRevision, Template,
    MediaAssociation, template_type)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, response)

from settings import (BASE_URL, _sep)
# TODO: replace _sep with proper urllib function

import re, datetime
from os.path import exists as _exists
from os import makedirs

media_buttons = '''
<button type="button" id="modal_close_button" class="btn btn-default" data-dismiss="modal">Close</button>
<button type="button" {} class="btn btn-primary">{}</button>
'''

def html_editor_settings(blog):
    try:
        html_editor_settings = Template.get(
            Template.blog == blog,
            Template.title == 'HTML Editor Init',
            Template.template_type == template_type.system
            ).body
    except Template.DoesNotExist:
        from core.static import html_editor_settings

    return html_editor_settings


# TODO: page-locking algorithm
@transaction
def page_edit(page_id):
    '''
    UI for editing a page in a blog
    '''
    user = auth.is_logged_in(request)
    page = Page.load(page_id)
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
            message="Page <b>{}</b> created.".format(page.for_log))
        page.modified_date = datetime.datetime.utcnow()
        page.save(user)

    tags = template_tags(page=page,
        user=user,
        status=status)

    # from core.ui_kv import kv_ui
    from core.ui import kv
    kv_ui_data = kv.ui(page.kv_list())

    tpl = template('edit/page',
        menu=generate_menu('edit_page', page),
        parent_path=referer,
        search_context=(search_context['blog'], page.blog),
        html_editor_settings=html_editor_settings(page.blog),
        sidebar=sidebar.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action_list=save_action_list,
            save_action=save_action,
            kv_ui=kv_ui_data,
            kv_object='Page',
            kv_objectid=page.id,
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
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    page.delete_preview()

    tags = cms.save_page(page, user, page.blog)

    from core.cms import save_action_list

    from core.ui import kv
    kv_ui_data = kv.ui(page.kv_list())

    tpl = template('edit/page_ajax',
        sidebar=sidebar.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui=kv_ui_data,
            kv_object='Page',
            kv_objectid=page.id,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl


@transaction
def page_delete(page_id, confirm):
    '''
    Deletes a selected page -- no confirmation yet
    Returns user to list of pages in blog with a notice about the deleted file
    '''

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)
    blog = page.blog

    from core.utils import Status

    tags = template_tags(
        page=page,
        user=user)

    from core.models import page_status

    if page.status != page_status.unpublished:
        message = 'Page <b>{}</b> is not set to unpublished and cannot be deleted. Unpublish this page before deleting it.'.format(
            page.for_display)
        url = '{}/blog/{}'.format(BASE_URL, blog.id)
        action = 'Return to the page listing'

        tags.status = Status(
            type='danger',
            no_sure=True,
            message=message,
            action=action,
            url=url,
            close=False)

    else:
        if request.forms.getunicode('confirm') == user.logout_nonce:

            p = page.for_log
            from core.cms import delete_page
            delete_page(page)

            message = 'Page {} successfully deleted'.format(
                p)
            url = '{}/blog/{}'.format(BASE_URL, blog.id)
            action = 'Return to the page listing'

            tags.status = Status(
                type='success',
                message=message,
                action=action,
                url=url,
                close=False)

            logger.info("Page {} deleted by user {}.".format(
                p,
                user.for_log))


        else:
            message = ('You are about to delete page <b>{}</b> from blog <b>{}</b>.'.format(
                page.for_display,
                blog.for_display))

            yes = {
                    'label':'Yes, delete this page',
                    'id':'delete',
                    'name':'confirm',
                    'value':user.logout_nonce}
            no = {
                'label':'No, return to blog page listing',
                'url':'{}/blog/{}'.format(
                    BASE_URL, blog.id)
                }

            tags.status = Status(
                message=message,
                type='warning',
                close=False,
                yes=yes,
                no=no
            )

    tpl = template('listing/report',
        menu=generate_menu('blog_delete_page', page),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def page_preview(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    preview_file = page.preview_file
    preview_fileinfo = page.default_fileinfo
    split_path = preview_fileinfo.file_path.rsplit('/', 1)

    preview_fileinfo.file_path = (
         split_path[0] + "/" +
         preview_file
         )

    page_tags = cms.generate_page_tags(preview_fileinfo, page.blog)
    file_page_text = cms.generate_page_text(preview_fileinfo, page_tags)
    cms.write_file(file_page_text, page.blog.path, preview_fileinfo.file_path)

    utils.disable_protection()

    from settings import DESKTOP_MODE, BASE_URL_ROOT

    if DESKTOP_MODE:
        page_url = BASE_URL_ROOT + "/" + preview_fileinfo.file_path + "?_={}".format(
            page.blog.id)
    else:
        page_url = preview_fileinfo.url.rsplit('/', 1)[0] + '/' + preview_file

    from core.libs.bottle import redirect
    redirect ("{}?_={}".format(
        page_url,
        page.modified_date.microsecond
        ))



@transaction
def delete_page_preview(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    # from core.mgmt import delete_page_preview
    # delete_page_preview(page)
    page.delete_preview()


@transaction
def page_revisions(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
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
    page = Page.load(page_id)
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
        file_path = page.blog.path + _sep + page.blog.media_path + _sep + x.filename
        if _exists(file_path):
            pass
        else:
            pass

@transaction
def page_media_upload(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    overwrite = []

    for n in request.files:
        x = request.files.get(n)
        media_path = page.blog.path + _sep + page.blog.media_path
        file_path = media_path + _sep + x.filename
        if _exists(file_path):
            from core.error import FileExistsError
            raise FileExistsError("File '{}' already exists on the server.".format(
                utils.html_escape(x.filename)))
        else:
            cms.register_media(x.filename, file_path, user, page=page)
            if not _exists(media_path):
                makedirs(media_path)
            x.save(file_path)

    tags = template_tags(page_id=page_id)

    return template('edit/page_media_list.tpl',
        **tags.__dict__)

@transaction
def page_media_delete(page_id, media_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    media = Media.load(media_id)
    media_reference = MediaAssociation.get(
        MediaAssociation.page == page,
        MediaAssociation.media == media)
    media_reference.delete_instance(recursive=True,
        delete_nullable=True)

    tags = template_tags(page=page)

    return template('edit/page_media_list.tpl',
        **tags.__dict__)

@transaction
def page_media_add(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    media_list = Media.select().where(
        Media.blog == page.blog)

    tags = template_tags(page=page,
        user=user)

    return template('modal/modal_images.tpl',
        media_list=media_list,
        title="Select image",
        buttons='',
        **tags.__dict__)


def page_get_media_templates(page_id, media_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    media = Media.load(media_id, page.blog)

    media_templates = Template.select().where(
        Template.blog == page.blog,
        Template.template_type == template_type.media).order_by(Template.title)

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
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)

    media = Media.load(media_id, page.blog)

    media_template = Template.get(
        Template.id == template_id)

    generated_template = utils.tpl(media_template.body,
        media=media)

    if media not in page.media:
        media.associate(page)

    return generated_template

@transaction
def page_revision_restore(page_id, revision_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)
    page_revision = PageRevision.select().where(PageRevision.id == revision_id).get()

    status = utils.Status(
        type='success',
        message='Page <b>{}</b> has been restored from backup dated {}.'.format(page.for_log,
            page_revision.modified_date)
        )

    tags = template_tags(page_id=page_id,
        user=user,
        status=status)

    page_revision.id = page.id
    tags.page = page_revision

    referer = BASE_URL + "/blog/" + str(page.blog.id)

    from core.cms import save_action_list
    # from core.ui_kv import kv_ui
    from core.ui import kv
    kv_ui_data = kv.ui(page.kv_list())
    # TODO: save action from this doesn't trigger queue run

    tpl = template('edit/page',
        status_badge=status_badge,
        save_action=save_action,
        menu=generate_menu('edit_page', page),
        search_context=(search_context['blog'], page.blog),
        html_editor_settings=html_editor_settings(page.blog),
        sidebar=sidebar.render_sidebar(
            panel_set='edit_page',
            status_badge=status_badge,
            save_action=save_action,
            save_action_list=save_action_list,
            kv_ui=kv_ui_data,
            kv_object='Page',
            kv_objectid=page.id,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl

@transaction
def page_revision_restore_save(page_id):

    user = auth.is_logged_in(request)
    page = Page.load(page_id)
    permission = auth.is_page_editor(user, page)
    tags = cms.save_page(page, user, page.blog)

    from core.cms import save_action_list

    tpl = template('edit/page_ajax',
        status_badge=status_badge,
        save_action=save_action,
        save_action_list=save_action_list,
        sidebar='',
        **tags.__dict__)

    response.add_header('X-Redirect', BASE_URL + '/page/{}/edit'.format(str(tags.page.id)))

    return tpl
