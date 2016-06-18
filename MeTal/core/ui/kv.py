from core.models.transaction import transaction
from core.libs.bottle import (template)

def kv_page_response(page_id):

    from core.ui_kv import kv_ui
    from core.models import template_tags

    tags = template_tags(page_id=page_id)

    # kv_ui_data = kv_ui(tags.page.kvs(no_traverse=True))
    kv_ui_data = kv_ui(tags.page.kv_list())

    tpl = template('sidebar/sidebar_page_kv_ui',
        kv_ui=kv_ui_data,
        **tags.__dict__)

    return tpl

from core.libs.bottle import (request)
from core import auth

@transaction
def add_kv():

    user = auth.is_logged_in(request)

    object = request.forms.getunicode('object')
    object_id = int(request.forms.getunicode('objectid'))

    key = request.forms.getunicode('new_key_name')
    value = request.forms.getunicode('new_key_value')

    from core import models
    object_to_add_to = models.__dict__[object]
    object_instance = object_to_add_to.get(
        object_to_add_to.id == object_id)

    security = auth.__dict__[object_to_add_to.security](user, object_instance)

    # TODO: replace with kv_add
    added_kv = object_instance.add_kv(
        object=object,
        objectid=object_id,
        key=key,
        value=value)

    return obj_map[object](object_id)

@transaction
def remove_kv():

    user = auth.is_logged_in(request)

    object_id = int(request.forms.getunicode('kv'))

    from core.models import KeyValue

    object_type = KeyValue.get(
        KeyValue.id == object_id)

    from core import models
    object_to_delete_from = models.__dict__[object_type.object]
    object_instance = object_to_delete_from.get(
        object_to_delete_from.id == object_id)

    security = auth.__dict__[object_to_delete_from.security](user, object_instance)

    # TODO: replace with kv_del?
    kv_delete = KeyValue.delete().where(
        KeyValue.id == object_id)

    kv_deleted = kv_delete.execute()

    return obj_map[object_type.object](object_type.objectid)

obj_map = {'Page': kv_page_response}
