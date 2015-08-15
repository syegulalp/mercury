from core.models import template_tags, FileInfo, Template, TemplateMapping, publishing_mode
from core.utils import is_blank
from core.log import logger
from core.cms import build_mapping_xrefs
from core.error import TemplateSaveException

def delete(template):

    t0 = FileInfo.delete().where(FileInfo.template_mapping << template.mappings)
    t0.execute()
    t1 = TemplateMapping.delete().where(TemplateMapping.id << template.mappings)
    t1.execute()
    t2 = Template.delete().where(Template.id == template.id)
    t2.execute()

def save(request, user, cms_template):

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

    cms_template.save()

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
                    raise TemplateSaveException('Template mapping #{} ({}) cannot be blank.'.format(
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
    tags = template_tags(template_id=cms_template.id,
                            user=user)


    if int(_forms.getunicode('save')) == 2:
        from core import cms
        for f in cms_template.fileinfos_published:
            cms.push_to_queue(job_type=f.template_mapping.template.template_type,
                blog=cms_template.blog,
                site=cms_template.blog.site,
                data_integer=f.id)

        status += " {} files regenerated from template.".format(
            cms_template.fileinfos_published.count())

    logger.info("Template {} edited by user {}.".format(
        cms_template.for_log,
        user.for_log))

    return status
