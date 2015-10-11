from core.models.transaction import transaction

from core.libs.bottle import (template, request)
from core import auth

def kv_page_response(page_id):

    from core.ui_kv import kv_ui
    from core.models import template_tags

    tags = template_tags(page_id=page_id)
    kv_ui_data = kv_ui(tags.page.kvs(no_traverse=True))

    tpl = template('sidebar/sidebar_page_kv_ui',
        kv_ui=kv_ui_data,
        **tags.__dict__)

    return tpl

obj_map = {'Page': kv_page_response}

@transaction
def add_kv():

    user = auth.is_logged_in(request)

    object = request.forms.getunicode('object')
    objectid = int(request.forms.getunicode('objectid'))

    # TODO: do security lookup with object type

    key = request.forms.getunicode('new_key_name')
    value = request.forms.getunicode('new_key_value')

    from core import models
    object_to_add = models.__dict__[object]()

    added_kv = object_to_add.add_kv(
        object=object,
        objectid=objectid,
        key=key,
        value=value)

    return obj_map[object](objectid)

@transaction
def remove_kv():

    user = auth.is_logged_in(request)

    object_id = int(request.forms.getunicode('kv'))

    # TOOD: do security lookup with object type

    from core.models import KeyValue

    object_type = KeyValue.get(
        KeyValue.id == object_id)

    kv_delete = KeyValue.delete().where(
        KeyValue.id == object_id)

    kv_deleted = kv_delete.execute()

    return obj_map[object_type.object](object_type.objectid)
