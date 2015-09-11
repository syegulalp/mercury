blank_item = '''
<li class="list-group-item">
<span
      title="Select {}"
      class="glyphicon glyphicon-plus-sign media-selector"></span>
{}<a href="#" title="Remove item"><span class="pull-right glyphicon glyphicon-remove media-remove"></span></a></li>
'''

media_item = '''
<li class="list-group-item" data-toggle="tooltip" data-placement="left"
      data-html="true"
      title="<div style='background-color:white'><img style='max-height:50px;' src='{}'></div>">
      <span
      title="Select media"
      class="glyphicon glyphicon-plus-sign media-selector"></span>
      {}:
      <a href="#" title="Remove media"><span class="pull-right glyphicon glyphicon-remove media-remove"></span></a>
      <a target="_blank" href="{}">{}</a>
</li>'''

def kv_ui(keys):

    kv_ui = []

    for n in keys:

        if n.is_schema is True:
            m = n
            # chooser only
            kv_ui.append(blank_item.format(
                "text",
                "{}: {}".format(n.key, n.value)))
        else:
            # chooser and existing kv
            m = n.key_parent if n.key_parent is not None else n

            if m.value_type == "Media":
                from core.models import Media
                p = Media.get(Media.id == n.value)
                kv_ui.append(media_item.format(
                    p.preview_url,
                    m.value,
                    p.link_format,
                    p.friendly_name))
            elif m.value_type == "User":
                from core.models import get_user
                user_obj = get_user(user_id=int(n.value))
                kv_ui.append(blank_item.format(
                    "user",
                    "{}: {}".format(m.value, user_obj.name)))


    return ''.join(kv_ui)
