from core.models.transaction import transaction
from core.libs.bottle import (template)

def kv_response(object_name, object_type, object_identifier, object_id):
    # from core.ui_kv import kv_ui
    from core.ui import kv
    from core.models import template_tags

    tag_args = {}
    tag_args[object_identifier] = object_id
    tags = template_tags(**tag_args)
    kv_ui_data = kv.ui(tags.__dict__[object_type].kv_list())

    tpl = template('sidebar/kv',
        kv_ui=kv_ui_data,
        kv_object=object_name,
        kv_objectid=object_id,
        **tags.__dict__)

    return tpl


objmap = {
    'Page':('page', 'page_id'),
    'Media':('media', 'media_id'),
    'Category':('category', 'category_id')
    }


from core.libs.bottle import (request)
from core import auth

@transaction
def kv_edit(kv_id):
    user = auth.is_logged_in(request)

    from core import models

    kv = models.KeyValue.get(
        models.KeyValue.id == kv_id)

    object_with_kv = models.__dict__[kv.object]

    object_instance = object_with_kv.get(
        object_with_kv.id == kv.objectid)

    security = auth.__dict__[object_with_kv.security](user, object_instance)

    if request.method == 'POST':
        kv.key = request.forms.getunicode('key')
        kv.value = request.forms.getunicode('value')
        kv.save()
        return kv_response(kv.object, objmap[kv.object][0],
            objmap[kv.object][1], object_instance.id)

        # return kv_list from kv_response above

    from core.ui.page import media_buttons
    buttons = media_buttons.format(
        'onclick="save_kv_changes();"',
        'Save changes')

    tpl = template('modal/modal_kv_edit',
        key=kv.key,
        value=kv.value,
        kv=kv,
        title='Edit KV #{} (on {} #{})'.format(kv.id,
            kv.object, kv.objectid),
        buttons=buttons
        )

    # save button formatting is odd, fix that
    return tpl

@transaction
def kv_add():

    user = auth.is_logged_in(request)

    kv_object = request.forms.getunicode('kv_object')
    kv_object_id = int(request.forms.getunicode('kv_objectid'))

    key = request.forms.getunicode('kv_new_key_name')
    value = request.forms.getunicode('kv_new_key_value')

    from core import models
    object_to_add_to = models.__dict__[kv_object]
    object_instance = object_to_add_to.get(
        object_to_add_to.id == kv_object_id)

    security = auth.__dict__[object_to_add_to.security](user, object_instance)

    added_kv = object_instance.kv_set(
        # object=kv_object,
        # objectid=kv_object_id,
        key=key,
        value=value)

    return kv_response(kv_object, objmap[kv_object][0],
        objmap[kv_object][1], kv_object_id)
    # return obj_map[kv_object](kv_object_id)

@transaction
def kv_remove():

    user = auth.is_logged_in(request)

    kv_to_delete = int(request.forms.getunicode('kv'))

    from core.models import KeyValue

    object_type = KeyValue.get(
        KeyValue.id == kv_to_delete)

    from core import models
    object_to_delete_from = models.__dict__[object_type.object]
    object_instance = object_to_delete_from.get(
        object_to_delete_from.id == object_type.objectid)

    security = auth.__dict__[object_to_delete_from.security](user, object_instance)

    # TODO: replace with kv_del?
    kv_delete = KeyValue.delete().where(
        KeyValue.id == kv_to_delete)

    kv_deleted = kv_delete.execute()


    return kv_response(object_type.object, objmap[object_type.object][0],
        objmap[object_type.object][1], object_instance.id)


from core.utils import html_escape

blank_item = '''
<li class="list-group-item wrap-txt">
<a onclick="remove_kv({});" href="#" title="Remove key/value pair"><span class="pull-right glyphicon glyphicon-remove media-remove"></span></a>{}</li>
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

def ui(keys):

    if keys is None:
        return None

    kv_ui = []

    for n in keys:

        kv_ui.append(blank_item.format(
            n.id,
            "<b><a title=\"Edit\" onclick=\"edit_kv({});\" href=\"#\">{}</a>:</b> <i>{}</i>".format(
                n.id,
                html_escape(n.key), html_escape(n.value))
            ))

    return ''.join(kv_ui)
