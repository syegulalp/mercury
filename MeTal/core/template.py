from core.models import Template
import re

include_re = re.compile("\{\{incl(.*?)\}\}")

def expand_includes(template_obj):
    
    template = template_obj.body
    blog = template_obj.blog
    
    while True:
        
        n = re.search(include_re, template)
        if n is None:
            break
        
        template_title = n.group(1)[2:][:-2]
        
        template_text = Template.get(
            Template.blog == blog,
            Template.title == template_title,
            Template.is_include == True
            )
        
        template = re.sub(include_re, template_text.body, template,
            count=1)

    return template

def list_includes(template_obj):
    pass