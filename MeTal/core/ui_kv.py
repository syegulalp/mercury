blank_item = '''
<li class="list-group-item">
<span
      title="Select {}"
      class="glyphicon glyphicon-plus-sign media-selector"></span>
{}</li>
'''

media_item = '''
<li class="list-group-item" data-toggle="tooltip" data-placement="left"
      data-html="true"
      title="<div style='background-color:white'><img style='max-height:50px;' src='{}'></div>">
      {}:
      <span
      title="Select media"
      class="glyphicon glyphicon-plus-sign media-selector"></span>
      <a href="#" title="Remove media"><span class="pull-right glyphicon glyphicon-remove media-remove"></span></a>      
      <a target="_blank" href="{}">{}</a>
</li>'''

def kv_ui(keys):
    
    kv_ui = []
    
    for n in keys:
        if n.is_schema is True:
            if n.value_type in "Media":
                kv_ui.append(blank_item.format(
                    "media",
                    n.value))
            if n.value_type == "User":
                kv_ui.append(blank_item.format(
                    "user",
                    n.value))
                
        else:
            if n.parent.value_type == "Media":
                from core.models import Media
                m = Media.get(Media.id == n.value)
                kv_ui.append(media_item.format(
                    m.preview_url,
                    n.parent.value,
                    m.link_format,
                    m.friendly_name))

    return ''.join(kv_ui)