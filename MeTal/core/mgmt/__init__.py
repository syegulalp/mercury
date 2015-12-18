import os, datetime, json

from settings import (APPLICATION_PATH, EXPORT_FILE_PATH, BASE_URL, DB, _sep)


from core.utils import Status, encrypt_password, is_blank
from core.log import logger

from core.models import (TemplateMapping, Template, System, KeyValue,
    Permission, Site, Blog, User, Category, Theme, Tag, get_default_theme)

from core.libs.playhouse.dataset import DataSet


def login_verify(email, password):

    try:
        user = User.get(User.email == email,
            User.password == encrypt_password(password))

    except User.DoesNotExist:
        raise User.DoesNotExist

    else:
        user.last_login = datetime.datetime.utcnow()
        user.save()
        return user

# move this into the theme schema object,
# or at least the theme module

# for deleting kvs automatically with their attendant object,
# we should have overload the delete function in the model

def get_kvs_for_theme(theme):
    from core.theme import json_dump
    theme_kvs = []

    kv_list = []

    top_kvs = KeyValue.select().where(
        KeyValue.object == 'Theme',
        KeyValue.objectid == theme.id,
        KeyValue.is_schema == True)

    for n in top_kvs:
        kv_list.append(n)

    while len(kv_list) > 0:
        theme_kvs.append(kv_list[0].id)
        next_kvs = KeyValue.select().where(
            KeyValue.parent == kv_list[0],
            KeyValue.is_schema == True)
        for f in next_kvs:
            kv_list.append(f)
        del kv_list[0]

    return theme_kvs

# move to Queue.erase?

def erase_queue(blog=None):
    from core.models import Queue
    if blog is None:
        delete_queue = Queue.delete()
    else:
        delete_queue = Queue.delete().where(Queue.blog == blog)
    return delete_queue.execute()

# move to blog.erase_theme()

def erase_theme(blog):

    del_kvs = get_kvs_for_theme(blog.theme)
    kvs_to_delete = KeyValue.delete().where(KeyValue.id << del_kvs)
    p = kvs_to_delete.execute()

    mappings_to_delete = TemplateMapping.delete().where(TemplateMapping.id << blog.template_mappings())
    m = mappings_to_delete.execute()
    templates_to_delete = Template.delete().where(Template.id << blog.templates())
    n = templates_to_delete.execute()
    return p, m, n


# since we return a theme instance anyway,
# why not Theme.install_to_system?

def theme_install_to_system(theme_data):

    json_raw = theme_data.decode('utf-8')
    json_obj = json.loads(json_raw)

    new_theme = Theme(
        title=json_obj["title"],
        description=json_obj["description"],
        json=json_raw
        )

    new_theme.save()
    return new_theme

# move to theme or blog?
# or make into blog.apply_theme?

def theme_apply_to_blog(theme, blog, user):
    '''
    Applies a given theme to a given blog.
    Removes and regenerates fileinfos for the pages on the blog.
    '''

    from core import cms
    cms.purge_fileinfos(blog.fileinfos)
    erase_theme(blog)
    theme_install_to_blog(theme, blog, user)

# same as above - blog.install_theme?

def theme_install_to_blog(installed_theme, blog, user):

    json_obj = json.loads(installed_theme.json)
    templates = json_obj["data"]
    kvs = json_obj["kv"]

    # theme_ids = {}

    for t in templates:

        template = templates[t]["template"]
        table_obj = Template()

        for name in table_obj._meta.fields:
            if name not in ("id"):
                setattr(table_obj, name, template[name])

        table_obj.blog = blog
        table_obj.save(user)

        mappings = templates[t]["mapping"]

        for mapping in mappings:
            mapping_obj = TemplateMapping()

            for name in mapping_obj._meta.fields:
                if name not in ("id"):
                    setattr(mapping_obj, name, mappings[mapping][name])

            mapping_obj.template = table_obj.id
            mapping_obj.save()

    kv_index = {}
    kx = System()

    # system KVs
    # replace this and the other with a general loop routine
    # that takes action based on what the object type is
    # keep that object type action with the schema itself
    # perhaps on_install_kv or something

    # ugh, the list is random, isn't it?
    # start with System, work our way DOWN through the object hierarchy
    # System - as-is
    # Theme - set to installed theme ID
    # Blog - set to installed blog ID
    # everything else - parent appropriately and preserve

    for kv in kvs:
        kv_current = kvs[kv]
        new_kv = kx.add_kv(**kv_current)
        kv_index[kv_current['id']] = new_kv.id

    for kv in kv_index:
        kv_current = kv
        new_kv_value = kv_index[kv]

        kv_to_change = KeyValue.get(
            KeyValue.id == new_kv_value)

        parent = kv_to_change.__dict__['_data']['parent']

        if parent is None:
            continue

        kv_to_change.parent = kv_index[parent]
        kv_to_change.save()

    from core import cms
    cms.purge_blog(blog)

    blog.theme = installed_theme.id

# to be handled by Site.save()

def site_create(**new_site_data):

    new_site = Site()

    new_site.name = new_site_data['name']
    new_site.description = new_site_data['description']
    new_site.url = new_site_data['url']
    new_site.path = new_site_data['path']
    new_site.local_path = new_site.path

    new_site.save()

    return new_site

def export_data():

    n = ("Beginning export process. Writing files to {}.".format(APPLICATION_PATH + EXPORT_FILE_PATH))

    yield ("<p>" + n)

    # db = DataSet('sqlite:///' + DATABASE_PATH)
    db = DataSet(DB.dataset_connection())

    if os.path.isdir(APPLICATION_PATH + EXPORT_FILE_PATH) is False:
            os.makedirs(APPLICATION_PATH + EXPORT_FILE_PATH)

    with db.transaction():

        for table_name in db.tables:

            if not table_name.startswith("page_search"):

                table = db[table_name]
                n = "Exporting table: " + table_name

                yield ('<p>' + n)
                filename = APPLICATION_PATH + EXPORT_FILE_PATH + '/dump-' + table_name + '.json'
                table.freeze(format='json', filename=filename)


    db.close()

    n = "Export process ended. <a href='{}'>Click here to continue.</a>".format(BASE_URL)

    yield ("<p>" + n)

def import_data():

    n = ("Beginning import process.")

    yield "<p>" + n

    DB.clean_database()

    xdb = DataSet(DB.dataset_connection())

    xdb.query(DB.pre_import(), commit=False)

    with xdb.transaction() as txn:

        for table_name in xdb.tables:

            xdb.query('DELETE FROM `{}`;'.format(table_name), commit=True)

    with xdb.transaction() as txn:

        for table_name in xdb.tables:

            n = ("Loading table " + table_name)

            yield "<p>" + n

            try:
                table = xdb[table_name]
            except:
                yield ("<p>Sorry, couldn't create table ", table_name)
            else:

                filename = (APPLICATION_PATH + EXPORT_FILE_PATH +
                    '/dump-' + table_name + '.json')
                if os.path.exists(filename):

                    table.thaw(format='json',
                        filename=filename,
                        strict=True)

                else:
                    n = ("No data for table " + table_name)
                    yield "<p>" + n

    xdb.query(DB.post_import())

    xdb.close()

    DB.recreate_indexes()

    n = "Import process ended. <a href='{}'>Click here to continue.</a>".format(BASE_URL)

    yield "<p>" + n

    from core.routes import app
    app.reset()


def add_user_permission(user, **permission):

    new_permission = Permission(
        user=user,
        permission=permission['permission'],
        site=permission['site'],
        )

    try:
        new_permission.blog = permission['blog']
    except KeyError:
        pass

    new_permission.save()

    return new_permission

# move to User.remove_permission()

def remove_user_permissions(user, permission_ids):
    from core import auth
    remove_permission = Permission.delete().where(
        Permission.id << permission_ids)
    done = remove_permission.execute()

    try:
        no_sysop = auth.get_users_with_permission(auth.role.SYS_ADMIN)
    except IndexError:
        from core.error import PermissionsException
        raise PermissionsException('You have attempted to delete the last known SYS_ADMIN privilege in the system. There must be at least one user with the SYS_ADMIN privilege.')

    return done

# move to Page.delete_preview()

def delete_page_preview(page):

    preview_file = page.preview_file
    preview_fileinfo = page.default_fileinfo
    split_path = preview_fileinfo.file_path.rsplit('/', 1)

    preview_fileinfo.file_path = preview_fileinfo.file_path = (
         split_path[0] + "/" +
         preview_file
         )

    import os

    try:
        return os.remove(page.blog.path + _sep + preview_fileinfo.file_path)
    except OSError as e:
        from core.error import not_found
        if not_found(e) is False:
            raise e
    except Exception as e:
        raise e
