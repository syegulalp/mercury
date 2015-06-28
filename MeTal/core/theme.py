 
def default(obj):
    import datetime

    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d %H:%M:%S')

def export_theme_for_blog(blog_id):
    import json
    from models import Template, TemplateMapping
    from libs.playhouse.shortcuts import model_to_dict
    
    theme_to_export = Template.select().where(
        Template.blog == blog_id)
    
    theme = {}
    theme["title"] = theme_to_export[0].theme.title
    theme["description"] = theme_to_export[0].theme.description
    theme["data"] = {}
    
    for n in theme_to_export:
        theme["data"][n.id] = {}
        
        theme["data"][n.id]["template"] = json.loads(json.dumps(model_to_dict(n, recurse=False),
            default=default,
            separators = (', ', ': '),
            indent=1))
        
        mappings_to_export = TemplateMapping.select().where(
            TemplateMapping.template == n)
        
        theme["data"][n.id]["mapping"]={}
        
        for m in mappings_to_export:
        
            theme["data"][n.id]["mapping"][m.id] = json.loads(json.dumps(model_to_dict(m, recurse=False),
                default=default,
                separators = (', ', ': '),
                indent=1))

        
    return theme
