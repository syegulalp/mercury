from core.models import template_tags, TemplateMapping
from core.utils import Status, is_blank
from core.log import logger

def save(request, user, cms_template):

    errors = []

    _forms = request.forms

    # TODO: any changes to the template name should alert the user?
    # checking against includes is likely to be really labor-intensive

    cms_template.title = _forms.getunicode('template_title')
    cms_template.body = _forms.getunicode('template_body')

    if is_blank(cms_template.title):
        cms_template.title = "New Template (#{})".format(
            cms_template.id)

    from core.models import publishing_modes
    mode = _forms.getunicode('publishing_mode')

    if mode in publishing_modes:
        cms_template.publishing_mode = mode
    else:
        errors.append("Invalid publishing mode selected.")

    if len(errors) == 0:
        cms_template.save()

    for n in _forms:
        if n.startswith('template_mapping_'):
            mapping_id = int(n[len('template_mapping_'):])
            try:
                template_mapping = TemplateMapping.get(
                    TemplateMapping.id == mapping_id
                    )
            except TemplateMapping.DoesNotExist:
                errors.append('Template mapping with ID #{} does not exist.'.format(
                    mapping_id))
            else:
                if is_blank(_forms.getunicode(n)):
                    errors.append('Template mapping #{} ({}) cannot be blank.'.format(
                        mapping_id,
                        template_mapping.path_string))
                else:
                    template_mapping.path_string = _forms.getunicode(n)
                    template_mapping.save()

                # TODO: we must validate this mapping to make sure it corresponds to something valid!
                # template_mapping.validate(path_string) ?
                # what context to give it?
                # index: blog
                # page: most recent blog page
                # archive: most recent blog page
                # includes: ??

    # TODO: eventually everything after this will be removed b/c of AJAX save
    tags = template_tags(template_id=cms_template.id,
                            user=user)

    if len(errors) == 0:

        # from core.models import page_status
        status = Status(
            type='success',
            message="Template <b>{}</b> saved.",
            vals=(cms_template.for_log,)
            )

        # regenerate templates
        if int(_forms.getunicode('save')) == 2:
            from core import cms
            for f in cms_template.fileinfos_published:
                cms.push_to_queue(job_type=cms_template.template_type,
                    priority=1,
                    blog=cms_template.blog,
                    site=cms_template.blog.site,
                    data_integer=f.id)

            status.message += " {} files regenerated from template.".format(
                cms_template.fileinfos_published.count())

    else:
        status = Status(
            type='danger',
            message="Error saving template <b>{}</b>: <br>{}",
            vals=(cms_template.for_log,
                ' // '.join(errors))
            )

    logger.info("Template {} edited by user {}.".format(
        cms_template.for_log,
        user.for_log))

    return status
