import json
from libs.playhouse.shortcuts import model_to_dict
 
def default(obj):
    import datetime

    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d %H:%M:%S')

def json_dump(obj):
    
    return json.loads(json.dumps(model_to_dict(obj, recurse=False),
            default=default,
            separators=(', ', ': '),
            indent=1))

def export_theme_for_blog(blog_id):
    
    from models import Template, TemplateMapping, KeyValue

    theme_to_export = Template.select().where(
        Template.blog == blog_id)
    
    theme = {}
    theme["title"] = theme_to_export[0].theme.title
    theme["description"] = theme_to_export[0].theme.description
    theme["data"] = {}
    
    for n in theme_to_export:
        theme["data"][n.id] = {}
        theme["data"][n.id]["template"] = json_dump(n)
        
        mappings_to_export = TemplateMapping.select().where(
            TemplateMapping.template == n)
        
        theme["data"][n.id]["mapping"] = {}
        
        for m in mappings_to_export:
            theme["data"][n.id]["mapping"][m.id] = json_dump(m)

    theme["kv"] = {}
    
    kv_list = []
    
    top_kvs = KeyValue.select().where(
        KeyValue.object == 'Theme',
        KeyValue.objectid == theme_to_export[0].theme.id,
        KeyValue.is_schema == True)
    
    for n in top_kvs:        
        kv_list.append(n)
    
    while len(kv_list) > 0:
        theme["kv"][kv_list[0].id] = json_dump(kv_list[0]) 
        next_kvs = KeyValue.select().where(
            KeyValue.parent == kv_list[0],
            KeyValue.is_schema == True)
        for f in next_kvs:
            kv_list.append(f)
        del kv_list[0]
        
    import settings
    with open(settings.APPLICATION_PATH + settings._sep + "install" + settings._sep + 
        "templates.json", "w", encoding='utf-8') as output_file:
        output_file.write(json.dumps(theme,
            indent=1,
            sort_keys=True,
            allow_nan=True))
        
    return theme

