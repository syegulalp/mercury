from core import (auth, utils, ui_mgr, template as _template)
from core.menu import generate_menu, icons

from core.models import (Blog,
    template_tags, Template,
    TemplateMapping, db, template_type, publishing_mode)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, redirect)

from . import search_context

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
    'Media':(),
    'System':()
    }


def new_template(blog_id, tpl_type):
    with db.atomic() as txn:

        user = auth.is_logged_in(request)
        blog = Blog.load(blog_id)
        permission = auth.is_blog_designer(user, blog)

        auth.check_template_lock(blog)

        mappings_index = template_mapping_index.get(tpl_type, None)
        if mappings_index is None:
            raise Exception('Mapping type not found')

        template = Template(
            blog=blog,
            theme=blog.theme,
            template_type=tpl_type,
            publishing_mode=publishing_mode.do_not_publish,
            body='',
            )
        template.save(user)
        template.title = 'Untitled Template #{}'.format(template.id)
        template.save(user)

        if tpl_type != template_type.media:

            new_template_mapping = TemplateMapping(
               template=template,
               is_default=True,
               path_string="'" + utils.create_basename(template.title, blog) + "'"
               )

            new_template_mapping.save()
            from core import cms
            cms.build_mapping_xrefs((new_template_mapping,))

    from settings import BASE_URL
    redirect(BASE_URL + '/template/{}/edit'.format(
        template.id))

@transaction
def template_edit(template_id):
    '''
    UI for editing a blog template
    '''

    user = auth.is_logged_in(request)
    edit_template = Template.load(template_id)
    blog = Blog.load(edit_template.blog.id)
    permission = auth.is_blog_designer(user, blog)

    auth.check_template_lock(blog)

    utils.disable_protection()

    tags = template_tags(template_id=template_id,
                        user=user)

    # find out if the template object returns a list of all the mappings, or just the first one
    # it's edit_template.mappings

    tags.mappings = template_mapping_index[edit_template.template_type]

    return template_edit_output(tags)

def template_refresh(template_id):
    user = auth.is_logged_in(request)
    tpl = Template.load(template_id)
    blog = Blog.load(tpl.blog)
    permission = auth.is_blog_designer(user, blog)

    from core.utils import Status
    import settings

    tags = template_tags(template_id=tpl.id,
        user=user)

    if request.forms.getunicode('confirm') == user.logout_nonce:

        import os, json
        template_path = (os.path.join(tpl.theme.path,
            tpl.template_ref))

        with open(template_path, 'r') as f:
            tp_json = json.loads(f.read())
            # TODO: We will eventually merge in all the other refresh functions
            # and convert this to a generic function called from
            # mgmt.theme_apply_to_blog as well
            with open(template_path[:-5] + '.tpl', 'r') as b:
                tpl.body = b.read()
            tpl.save(user)

        status = Status(
            type='success',
            close=False,
            message='Template <b>{}</b> was successfully refreshed from theme <b>{}</b>.'.format(
                tpl.for_display,
                tpl.theme.for_display),
            action='Return to template',
            url='{}/template/{}/edit'.format(
                settings.BASE_URL, tpl.id)
            )

    else:

        status = Status(
            type='warning',
            close=False,
            message='''
You are attempting to refresh template <b>{}</b> for blog <b>{}</b> from its underlying theme <b>{}</b>.</p>
<p>This will <b>overwrite</b> the current version of the template and replace it with the original version
from the theme.
'''.format(
                tpl.for_display,
                blog.for_display,
                tpl.theme.for_display),
            no={'url':'{}/template/{}/edit'.format(
                settings.BASE_URL, tpl.id),
                'label':'No, I don\'t want to replace this template'
                },
            yes={'id':'delete',
                'name':'confirm',
                'label':'Yes, I want to replace this template',
                'value':user.logout_nonce}
            )


    tags.status = status
    tplt = template('listing/report',
        menu=generate_menu('blog_delete_template', tpl),
        search_context=(search_context['blog'], blog),
        **tags.__dict__)

    return tplt



def template_delete(template_id):

    user = auth.is_logged_in(request)
    tpl = Template.load(template_id)
    blog = Blog.load(tpl.blog)
    permission = auth.is_blog_designer(user, blog)

    from core.utils import Status
    import settings

    tags = template_tags(template_id=tpl.id,
        user=user)

    if request.forms.getunicode('confirm') == user.logout_nonce:

        # _template.delete(tpl)
        tpl.delete_instance()

        status = Status(
            type='success',
            close=False,
            message='Template {} was successfully deleted.'.format(tpl.for_log),
            action='Return to template list',
            url='{}/blog/{}/templates'.format(
                settings.BASE_URL, blog.id)
            )

    else:

        status = Status(
            type='warning',
            close=False,
            message='You are attempting to delete template <b>{}</b> from blog <b>{}</b>.'.format(
                tpl.for_display,
                blog.for_display),
            no={'url':'{}/template/{}/edit'.format(
                settings.BASE_URL, tpl.id),
                'label':'No, I don\'t want to delete this template'
                },
            yes={'id':'delete',
                'name':'confirm',
                'label':'Yes, I want to delete this template',
                'value':user.logout_nonce}
            )


    tags.status = status
    tplt = template('listing/report',
        menu=generate_menu('blog_delete_template', tpl),
        search_context=(search_context['blog'], blog),
        **tags.__dict__)

    return tplt

@transaction
def template_edit_save(template_id):
    '''
    UI for saving a blog template
    '''
    user = auth.is_logged_in(request)
    tpl = Template.load(template_id)
    blog = Blog.load(tpl.blog)
    permission = auth.is_blog_designer(user, blog)

    auth.check_template_lock(blog)

    from core.utils import Status
    from core.error import TemplateSaveException, PageNotChanged

    status = None

    save_mode = int(request.forms.getunicode('save', default="0"))

    if save_mode in (1, 2, 3):
        try:
            message = _template.save(request, user, tpl, blog)
        except TemplateSaveException as e:
            status = Status(
                type='danger',
                no_sure=True,
                message="Error saving template <b>{}</b>:".format(tpl.for_display),
                message_list=(e,))
        except PageNotChanged as e:
            status = Status(
                type='success',
                message="Template <b>{}</b> was unchanged.".format(tpl.for_display)
                )

        except BaseException as e:
            raise e
            status = Status(
                type='warning',
                no_sure=True,
                message="Problem saving template <b>{}</b>: <br>".format(tpl.for_display),
                message_list=(e,))

        else:
            template_preview_delete(tpl)
            status = Status(
                type='success',
                message="Template <b>{}</b> saved successfully. {}".format(tpl.for_display,
                    message)  # TODO: move messages into message lister
                )

    tags = template_tags(template_id=template_id,
                        user=user)

    tags.mappings = template_mapping_index[tpl.template_type]

    tags.status = status

    from core.models import (template_type as template_types)

    tpl = template('edit/template_ajax',
        sidebar=ui_mgr.render_sidebar(
            panel_set='edit_template',
            publishing_mode=publishing_mode,
            types=template_types,
            **tags.__dict__
            ),
        **tags.__dict__)

    return tpl

def template_preview(template_id):

    from settings import _sep
    import os

    template = Template.load(template_id)

    if template.template_type == template_type.index:
        tags = template_tags(blog=template.blog,
            fileinfo=template.fileinfos[0])
    if template.template_type == template_type.page:
        tags = template_tags(page=template.blog.published_pages[0],
            fileinfo=template.blog.published_pages[0].fileinfos[0])
    if template.template_type == template_type.archive:
        from core.cms import generate_archive_context
        archive_pages = generate_archive_context(
            template.default_mapping.archive_xref,
            template.blog.published_pages,
            page=template.blog.published_pages[0]
            )
        tags = template_tags(blog=template.blog,
                archive=archive_pages,
                archive_context=template.default_mapping.fileinfos[0],
                fileinfo=template.default_mapping.fileinfos[0])

    tpl_output = utils.tplt(template, tags)

    preview = template.preview_path

    if os.path.isdir(preview['path']) is False:
        os.makedirs(preview['path'])

    with open(preview['path'] + _sep + preview['file'], "wb") as output_file:
        output_file.write(tpl_output.encode('utf8'))

    import settings
    if settings.DESKTOP_MODE:
        url = settings.BASE_URL_ROOT + '/' + preview['subpath'] + '/' + preview['file'] + '?_={}'.format(
            template.blog.id)
    else:
        url = template.blog.url + '/' + preview['subpath'] + '/' + preview['file']

    redirect (url)

def template_preview_delete(tpl):

    try:
        preview = tpl.preview_path
    except:
        return None

    if preview is None:
        return None

    from settings import _sep
    import os

    try:
        return os.remove(preview['path'] + _sep + preview['file'])
    except OSError as e:
        from core.error import not_found
        if not_found(e) is False:
            raise e

    except Exception as e:
        raise e

def template_edit_output(tags):

    from core.models import template_type as template_types

    tpl = template('edit/template',
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
