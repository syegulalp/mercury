from core.models.transaction import transaction
from core.libs.bottle import (template)

def kv_response(object_name, object_type, object_identifier, object_id):
    from core.ui_kv import kv_ui
    from core.models import template_tags

    tag_args = {}
    tag_args[object_identifier] = object_id
    tags = template_tags(**tag_args)
    kv_ui_data = kv_ui(tags.__dict__[object_type].kv_list())

    tpl = template('sidebar/sidebar_kv_ui',
        kv_ui=kv_ui_data,
        kv_object=object_name,
        kv_objectid=object_id,
        **tags.__dict__)

    return tpl


objmap = {
    'Page':('page', 'page_id'),
    'Media':('media', 'media_id')
    }


from core.libs.bottle import (request)
from core import auth

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

    # TODO: replace with kv_add
    added_kv = object_instance.kv_add(
        object=kv_object,
        objectid=kv_object_id,
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
