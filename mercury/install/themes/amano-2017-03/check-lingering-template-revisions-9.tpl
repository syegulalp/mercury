% from core.models import Template, TemplateRevision
% n = TemplateRevision.select().where(~TemplateRevision.template_id << Template.select(Template.id))
Templates with orphan revisions: {{n.count()}}<hr/>
% for m in n:
{{!m.title}}
% #m.delete_instance()
% end