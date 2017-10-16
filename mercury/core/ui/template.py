from core import (auth, utils)
from core.ui import sidebar
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
            from core.cms import fileinfo
            fileinfo.build_mapping_xrefs((new_template_mapping,))

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

@transaction
def template_set_default(template_id):
    '''
    UI for setting a given template as the default for an archive type
    '''

    user = auth.is_logged_in(request)
    tpl = Template.load(template_id)
    blog = Blog.load(tpl.blog.id)
    permission = auth.is_blog_designer(user, blog)

    auth.check_template_lock(blog)

    tags = template_tags(template=tpl,
                        user=user)

    from core.utils import Status
    import settings

    if request.forms.getunicode('confirm') == user.logout_nonce:

        # check for form submission
        # setting should be done by way of class object
        # theme? blog? template?
        # blog.set_default_archive_template(template,{archive_type.index...})

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
        tags.status = status
    else:
        pass

    from core.models import archive_defaults

    return template('edit/template-set-default',
        icons=icons,
        search_context=(search_context['blog'], tags.blog),
        menu=generate_menu('blog_edit_template', tags.template),
        sidebar=sidebar.render_sidebar(
            panel_set='edit_template',
            publishing_mode=publishing_mode,
            types=template_type,
            **tags.__dict__
            ),
        archive_defaults=archive_defaults,
        **tags.__dict__)


@transaction
def template_refresh(template_id):
    '''
    UI for reloading a template from the original version stored in the
    template's theme (assuming such an original template exists)
    '''
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

    return template('listing/report',
        menu=generate_menu('blog_delete_template', tpl),
        search_context=(search_context['blog'], blog),
        msg_float=False,
        **tags.__dict__)

@transaction
def template_delete(template_id):
    '''
    UI for deleting a template
    '''
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

    return template('listing/report',
        menu=generate_menu('blog_delete_template', tpl),
        search_context=(search_context['blog'], blog),
        msg_float=False,
        **tags.__dict__)



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
            message = template_save(request, user, tpl, blog)
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

        except Exception as e:
            raise e
            status = Status(
                type='warning',
                no_sure=True,
                message="Problem saving template <b>{}</b>: <br>".format(tpl.for_display),
                message_list=(e,))

        else:
            tpl.delete_preview()
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

    return template('edit/template_ajax',
        sidebar=sidebar.render_sidebar(
            panel_set='edit_template',
            publishing_mode=publishing_mode,
            types=template_types,
            **tags.__dict__
            ),
        **tags.__dict__)

def test_preview_mapping(fi, t):
    if fi == 0:
        from core.error import PreviewException
        raise PreviewException(
            'Template {} has no mapping associated with it and cannot be previewed.'.format(
            t.for_log))

def template_preview(template_id):
    '''
    Wrapper for previewing a template, as we need to elegantly handle any exceptions
    raised in the underlying process
    '''
    try:
        redirection = template_preview_core(template_id)
    except Exception as e:
        raise e
    else:
        redirect(redirection)

@transaction
def template_preview_core(template_id):
    '''
    UI for generating a preview of a given template
    '''
    from core.models import Page, FileInfo, page_status
    from core.cms import fileinfo
    from core.cms import invalidate_cache

    invalidate_cache()

    template = Template.load(template_id)

    # TODO: only rebuild mappings if the dirty bit is set

    if template.template_type == template_type.index:

        fi = template.default_mapping.fileinfos
        test_preview_mapping(fi.count(), template)
        fi = fi.get()
        tags = template_tags(blog=template.blog,
            template=template,
            fileinfo=fi
            )

    elif template.template_type == template_type.page:
        try:
            fi = Page.load(int(request.query['use_page'])).fileinfos[0]
        except (KeyError, TypeError):
            fi = template.fileinfos
            test_preview_mapping(fi.count(), template)
            fi = fi.select().join(Page).where(FileInfo.page == Page.id,
                Page.blog == template.blog,
                Page.status == page_status.published,
                ).order_by(Page.publication_date.desc()).get()
        tags = template_tags(
            template=template,
            page=fi.page,
            )

    elif template.template_type == template_type.include:
        if template.publishing_mode != publishing_mode.ssi:
            from core.error import PreviewException
            raise PreviewException('You can only preview server-side includes.')
        page = template.blog.pages.published.order_by(Page.publication_date.desc()).get()
        fi = page.fileinfos[0]
        tags = template_tags(
            template=template,
            page=page,
            )

    elif template.template_type == template_type.archive:

        if 'use_page' in request.query:
            page_list = [Page.load(int(request.query['use_page']))]
        elif 'use_category' in request.query:
            from core.models import Category
            page_list = Category.load(int(request.query['use_category'])).pages.published.limit(1)
        elif 'use_tag' in request.query:
            from core.models import Tag
            page_list = Tag.load(int(request.query['use_tag'])).pages.published.limit(1)
        else:
            page_list = template.blog.pages.published.limit(1)

#         try:
#             page_list = [Page.load(int(request.query['use_page']))]
#         except (KeyError, TypeError) as e:  # int from None, etc.
#             page_list = template.blog.pages.published.order_by(Page.publication_date.desc()).limit(1)

        fi = fileinfo.build_archives_fileinfos_by_mappings(template, pages=page_list)
        test_preview_mapping(len(fi), template)
        fi = fi[0]

        archive_pages = fileinfo.generate_archive_context_from_fileinfo(
            fi.xref.archive_xref, template.blog.pages.published, fi)

        tags = template_tags(
                blog=template.blog,
                archive=archive_pages,
                archive_context=fi,
                fileinfo=fi,
                template=template
                )

    elif template.template_type in (template_type.media, template_type.system):
        from core.error import PreviewException
        raise PreviewException('Template {} is of a type that cannot yet be previewed.'.format(
            template.for_log))

    import time
    from core.template import tplt
    tc = time.clock
    start = tc()
    tpl_output = tplt(template, tags)
    end = tc()

    tpl_output = r'<!-- Produced by template {}. Total render time:{} secs -->{}'.format(
        template.for_log,
        end - start,
        tpl_output)

    preview_file_path, preview_url = fi.make_preview()

    from core.cms import queue
    queue.write_file(tpl_output, template.blog.path, preview_file_path)

    return ("{}?_={}".format(
        preview_url,
        template.modified_date.microsecond
        ))

def template_edit_output(tags):

    return template('edit/template',
        icons=icons,
        search_context=(search_context['blog'], tags.blog),
        menu=generate_menu('blog_edit_template', tags.template),
        sidebar=sidebar.render_sidebar(
            panel_set='edit_template',
            publishing_mode=publishing_mode,
            types=template_type,
            **tags.__dict__
            ),
        **tags.__dict__)


@transaction
def template_save(request, user, cms_template, blog=None):
    '''
    Core logic for saving changes to a template.
    '''

    # TODO: move the bulk of this into the actual model
    # the .getunicode stuff should be moved out,
    # make that part of the ui
    # we should just submit cms_template as self,
    # make whatever mods to it are needed in the ui func,
    # and perform the validation we did elsewhere, perhaps

    from core.cms import fileinfo, invalidate_cache
    from core.utils import is_blank
    from core.error import TemplateSaveException, PageNotChanged
    import datetime

    status = []

    _forms = request.forms

    cms_template.title = _forms.getunicode('template_title')
    cms_template.body = _forms.getunicode('template_body')

    if is_blank(cms_template.title):
        cms_template.title = "New Template (#{})".format(
            cms_template.id)

    mode = _forms.getunicode('publishing_mode')

    if mode in publishing_mode.modes:
        cms_template.publishing_mode = mode
    else:
        raise TemplateSaveException("Invalid publishing mode selected.")

    cms_template.modified_date = datetime.datetime.utcnow()

    try:
        cms_template.save(user)
    except PageNotChanged as e:
        status.append("(Template unchanged.)")
    except Exception as e:
        raise e

    new_mappings = []

    for n in _forms:
        if n.startswith('template_mapping_'):
            mapping_id = int(n[len('template_mapping_'):])
            try:
                template_mapping = TemplateMapping.get(
                    TemplateMapping.id == mapping_id
                    )
            except TemplateMapping.DoesNotExist:
                raise TemplateSaveException('Template mapping with ID #{} does not exist.'.format(
                    mapping_id))
            else:
                if is_blank(_forms.getunicode(n)):
                    raise TemplateSaveException('Template mapping #{} ({}) cannot be blank. Use None to specify no mapping.'.format(
                        mapping_id,
                        template_mapping.path_string))
                else:
                    if _forms.getunicode(n) != template_mapping.path_string:
                        template_mapping.path_string = _forms.getunicode(n)
                        new_mappings.append(template_mapping)

    for n in new_mappings:
        n.save()
        status.append("Mapping #{} ({}) rebuilt.".format(
            n.id,
            n.path_string))


    if new_mappings:
        fileinfo.build_mapping_xrefs(new_mappings)
        build_action = "all"
    else:
        build_action = "fast"

    invalidate_cache()

    # TODO: eventually everything after this will be removed b/c of AJAX save
    # tags = template_tags(template_id=cms_template.id, user=user)

    save_action = _forms.getunicode('save')

    from core.libs.bottle import response
    from settings import BASE_URL
    from core.models import Queue

    x_open = False

    if int(save_action) in (2, 3):

        if cms_template.template_type == template_type.page:
            x_open = True
            response.add_header('X-Open',
                '{}/template/{}/queue/{}'.format(
                    BASE_URL, cms_template.id, build_action))

        if cms_template.template_type == template_type.archive:
            x_open = True
            response.add_header('X-Open',
                '{}/template/{}/queue/{}'.format(
                    BASE_URL, cms_template.id, build_action))
        if cms_template.template_type in (template_type.include, template_type.index):

            # I don't think this is needed anymore, we can remove it
            # TODO: test it
            # if new_mappings:
                # cms.build_archives_fileinfos_by_mappings(cms_template)

            for f in cms_template.fileinfos_published:
                Queue.push(job_type=f.template_mapping.template.template_type,
                    blog=cms_template.blog,
                    site=cms_template.blog.site,
                    data_integer=f.id)

        status.append("{} files regenerated from template and sent to publishing queue.".format(
            cms_template.fileinfos_published.count()))

    if blog is not None:
        blog.theme_modified = True
        blog.save()

    from core.log import logger
    logger.info("Template {} edited by user {}.".format(
        cms_template.for_log,
        user.for_log))

    response.body = ' '.join(status)

    if x_open:
        return response
    else:
        return response.body


