from core import (auth, utils, ui_mgr, template as _template)
from core.menu import generate_menu, icons

from core.models import (get_blog, get_template,
    template_tags, Template,
    TemplateMapping, db, template_type, publishing_mode)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, redirect)

from .ui import template_mapping_index, search_context

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
    from core.error import TemplateSaveException, PageNotChanged

    status = None

    save_mode = int(request.forms.getunicode('save', default="0"))

    if save_mode == 4:
        if request.forms.getunicode('confirm') == 'Y':
            return template_delete(template)
        else:
            status = Status(
                type='warning',
                message='You are attempting to delete this template. <b>Are you sure you want to do this?</b>',
                confirm=('save', '4')
                )

    if save_mode in (1, 2):
        try:
            message = _template.save(request, user, template)
        except TemplateSaveException as e:
            status = Status(
                type='danger',
                message="Error saving template <b>{}</b>:",
                vals=(template.for_log,),
                message_list=(e,))
        except PageNotChanged as e:
            status = Status(
                type='success',
                message="Template <b>{}</b> was unchanged.",
                vals=(template.for_log,)
                )

        except BaseException as e:
            status = Status(
                type='warning',
                message="Problem saving template <b>{}</b>: <br>",
                vals=(template.for_log,),
                message_list=(e,))

        else:
            status = Status(
                type='success',
                message="Template <b>{}</b> saved successfully. {}",
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
