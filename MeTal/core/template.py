# TODO: move all this out of here and into the schema
# delete will eventually just be subsumed into __del__ for the model, for instance?

from core.models import FileInfo, Template, TemplateMapping, TemplateRevision, publishing_mode
from core.utils import is_blank
from core.log import logger
from core.cms import build_mapping_xrefs
from core.error import TemplateSaveException
from core.error import PageNotChanged


def delete(template):
    return template.delete_instance()


def preview_path(template):
    return template.preview_path

def save(request, user, cms_template, blog=None):

    # TODO: move the bulk of this into the actual model
    # the .getunicode stuff should be moved out,
    # make that part of the ui
    # we should just submit cms_template as self,
    # make whatever mods to it are needed in the ui func,
    # and perform the validation we did elsewhere, perhaps

    import datetime

    status = ''

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
        status += "(Template unchanged.)"
    except BaseException as e:
        raise e

    mappings = []

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
                        # need to check for mapping validation
                        # if invalid, return some kind of warning
                        # not an exception per se?
                        # template_mapping.save()
                        mappings.append(template_mapping)

    for n in mappings:
        n.save()
        status += " Mapping #{} ({}) rebuilt.".format(
            n.id,
            n.path_string)
    build_mapping_xrefs(mappings)

    # TODO: eventually everything after this will be removed b/c of AJAX save
    # tags = template_tags(template_id=cms_template.id, user=user)

    save_action = _forms.getunicode('save')

    if int(save_action) in (2, 3):

        from core import cms
        cms.build_archives_fileinfos_by_mappings(cms_template)

        for f in cms_template.fileinfos_published:
            cms.push_to_queue(job_type=f.template_mapping.template.template_type,
                blog=cms_template.blog,
                site=cms_template.blog.site,
                data_integer=f.id)

        status += " {} files regenerated from template and sent to publishing queue.".format(
            cms_template.fileinfos_published.count())

    if blog is not None:
        blog.theme_modified = True
        blog.save()

    logger.info("Template {} edited by user {}.".format(
        cms_template.for_log,
        user.for_log))

    return status

