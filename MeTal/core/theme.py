 
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

    # save all master KVs that relate to this theme
    # cascade through all objects recursively, append them to a list
    # save the list as JSON
    
    # start at top of list
    # any children?
    # if so
        # add those to the list
        # write out the source's JSON
        # delete the source 
    # iterate until nothing left
    
    

    import settings
    with open(settings.APPLICATION_PATH+settings._sep+"install"+settings._sep+
        "templates.json", "w", encoding='utf-8') as output_file:
        output_file.write(json.dumps(theme,
            indent=1,
            sort_keys=True,
            allow_nan=True))
        
    return theme

