from core import (auth, utils, cms, ui_mgr)
from core.log import logger
from core.menu import generate_menu

from core.models import (get_blog, get_media,
    template_tags, get_page, Page, PageRevision, Template,
    MediaAssociation, Tag, template_type)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, response)

from settings import (BASE_URL, _sep)

import re, datetime, json
from os.path import exists as _exists
from os import makedirs

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
def register_plugin(plugin_path):
    from core.plugins import register_plugin, PluginImportError
    try:
        new_plugin = register_plugin(plugin_path)
    except PluginImportError as e:
        return (str(e))
    return ("Plugin " + new_plugin.friendly_name + " registered.")



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

    clean_preview = delete_page_preview(page_id)

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

    preview_file = page.preview_file
    preview_fileinfo = page.default_fileinfo
    split_path = preview_fileinfo.file_path.rsplit('/', 1)

    preview_fileinfo.file_path = preview_fileinfo.file_path = (
         split_path[0] + "/" +
         preview_file
         )

    cms.build_file(preview_fileinfo, page.blog)

    utils.disable_protection()

    import settings

    if settings.DESKTOP_MODE:
        page_url = settings.BASE_URL_ROOT + "/" + preview_fileinfo.file_path + "?_={}".format(
            page.blog.id)
    else:
        page_url = preview_fileinfo.url.rsplit('/', 1)[0] + '/' + preview_file

    tpl = template('ui/ui_preview',
        page=page,
        page_url=page_url)

    return tpl

@transaction
def delete_page_preview(page_id):

    user = auth.is_logged_in(request)
    page = get_page(page_id)
    permission = auth.is_page_editor(user, page)

    preview_file = page.preview_file
    preview_fileinfo = page.default_fileinfo
    split_path = preview_fileinfo.file_path.rsplit('/', 1)

    preview_fileinfo.file_path = preview_fileinfo.file_path = (
         split_path[0] + "/" +
         preview_file
         )

    import os
    try:
        os.remove(page.blog.path + _sep + preview_fileinfo.file_path)
    except BaseException as e:
        response.status = 500
        return str(e)

    return ''


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
        file_path = page.blog.path + _sep + page.blog.media_path + _sep + x.filename
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
        media_path = page.blog.path + _sep + page.blog.media_path
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
    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(page.kvs())

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
            kv_ui=kv_ui_data,
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


