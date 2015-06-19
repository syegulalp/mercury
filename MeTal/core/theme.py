def default(obj):
    import datetime

    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d %H:%M:%S')

def export_template_for_blog(blog_id):
    import json
    from models import Template
    from libs.playhouse.shortcuts import model_to_dict    

    export = []
    
    template_to_export = Template.select().where(
        Template.blog == blog_id)
    
    for n in template_to_export:
        
        export.append(json.dumps(model_to_dict(n, recurse=False),
            default=default,
            indent=1))
    
    return ''.join(export)
