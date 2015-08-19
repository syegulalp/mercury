from core.utils import Status, encrypt_password
from core.log import logger
import json

from core.models import (TemplateMapping, Template, System, KeyValue,
    Permission, Site, Blog, User, Category, Theme, get_theme)

from settings import (APPLICATION_PATH, EXPORT_FILE_PATH, BASE_URL, DB)

from core.libs.playhouse.dataset import DataSet

import os, datetime

def login_verify(email, password):

    try:
        user = User.get(User.email == email,
            User.password == encrypt_password(password))

    except User.DoesNotExist:
        raise User.DoesNotExist

    else:
        user.last_login = datetime.datetime.now()
        user.save()
        return user

def theme_delete(theme):
    pass
    # remove everything that has a dependency to this theme
    # TemplateMapping, Template, FileInfo, FileInfoContext
    # we should write a function to purge a template set from a blog
    # and invoke that

def theme_create(**new_theme_data):

    new_theme = Theme()

    new_theme.title = new_theme_data['title']
    new_theme.description = new_theme_data['description']
    new_theme.json = new_theme_data['json']

    new_theme.save()

    return new_theme

def theme_install_to_system(theme_data):

    json_raw = theme_data.decode('utf-8')
    json_obj = json.loads(json_raw)

    new_theme = theme_create(
        title=json_obj["title"],
        description=json_obj["description"],
        json=json_raw
        )

    return new_theme

def theme_apply_to_blog(theme, blog):
    '''
    Applies a given theme to a given blog.
    Removes and regenerates fileinfos for the pages on the blog.
    '''

    from core import cms
    cms.purge_fileinfos(blog.fileinfos)

    mappings_to_remove = TemplateMapping.delete().where(
        TemplateMapping.template << blog.templates)
    mappings_to_remove.execute()

    theme_to_remove = Template.delete().where(
        Template.blog == blog)
    theme_to_remove.execute()

    theme_install_to_blog(theme, blog)


def theme_install_to_blog(installed_theme, blog):

    json_obj = json.loads(installed_theme.json)
    templates = json_obj["data"]
    kvs = json_obj["kv"]

    for t in templates:

        template = templates[t]["template"]
        table_obj = Template()

        for name in table_obj._meta.fields:
            if name not in ("id"):
                setattr(table_obj, name, template[name])

        table_obj.theme = installed_theme
        table_obj.blog = blog
        table_obj.save()

        mappings = templates[t]["mapping"]

        for mapping in mappings:
            mapping_obj = TemplateMapping()

            for name in mapping_obj._meta.fields:
                if name not in ("id"):
                    setattr(mapping_obj, name, mappings[mapping][name])

            mapping_obj.template = table_obj
            mapping_obj.save()

    kv_index = {}
    kx = System()

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

    # TODO: use purge_blog instead

    # for n in blog.pages():
    cms.build_pages_fileinfos(blog.pages())

    # for n in blog.index_templates:
    cms.build_indexes_fileinfos(blog.index_templates)


def site_create(**new_site_data):

    new_site = Site()

    new_site.name = new_site_data['name']
    new_site.description = new_site_data['description']
    new_site.url = new_site_data['url']
    new_site.path = new_site_data['path']
    new_site.local_path = new_site.path

    new_site.save()

    return new_site


def blog_create(**new_blog_data):

    new_blog = Blog()

    new_blog.site = new_blog_data['site'].id
    new_blog.name = new_blog_data['name']
    new_blog.description = new_blog_data['description']
    new_blog.url = new_blog_data['url']
    new_blog.path = new_blog_data['path']
    new_blog.local_path = new_blog.path
    new_blog.theme = new_blog_data['theme']

    new_blog.save()

    new_blog_default_category = Category(
        blog=new_blog,
        title="Uncategorized",
        default=True)

    new_blog_default_category.save()

    # template installation should be its own function
    # install whatever the currently set system default templates are

    user = user_from_ka(**new_blog_data)

    logger.info("Blog {} created on site {} by user {}.".format(
        new_blog.for_log,
        new_blog.site.for_log,
        user.for_log))

    return new_blog

def user_from_ka(**ka):
    user = ka.get('user', User(id=0,
            name='[System]'))
    '''
    if 'user' in ka:
        return ka['user']
    else:
        user = User(id=0,
            name='[System]')
    '''
    return user


def blog_settings_save(request, blog, user):

        _forms = request.forms

        blog_name = _forms.getunicode('blog_name')

        if blog_name is not None:
            blog.name = blog_name

        blog_description = _forms.getunicode('blog_description')

        if blog_description is not None:
            blog.description = blog_description

        blog_url = _forms.getunicode('blog_url')

        if blog_url is not None:
            blog_url = blog_url.rstrip('/')
            blog.url = blog_url

        # TODO: url validation

        blog_path = _forms.getunicode('blog_path')
        if blog_path is not None:
            blog_path = blog_path.rstrip('/')
            blog.path = blog_path

        # TODO: validate this path

        blog_base_extension = _forms.getunicode('blog_base_extension')
        if blog_base_extension is not None:
            blog_base_extension = blog_base_extension.lstrip('.')
            blog.base_extension = blog_base_extension

        blog.save()

        status = Status(
            type='success',
            message="Settings for <b>{}</b> saved.",
            vals=(blog.name,))

        logger.info("Settings for blog {} edited by user {}.".format(
            blog.for_log,
            user.for_log))

        return status

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

def user_create(**new_user_data):

    new_user = User()

    new_user.name = new_user_data['name']
    new_user.email = new_user_data['email']

    if 'password' in new_user_data:
        new_user.password = encrypt_password(new_user_data['password'])
    elif 'encrypted_password' in new_user_data:
        new_user.password = new_user_data['encrypted_password']
    else:
        new_user.password = encrypt_password('Temporary password')

    new_user.save()

    return new_user

def create_user_blog(**new_user_data):

    new_user = user_create(**new_user_data)
    blog = new_user_data['blog']
    site = blog.site

    saved_permission = add_user_permission(new_user,
         permission=127,
         blog=blog,
         site=site)

    user = user_from_ka(**new_user_data)

    logger.info("User {} created on blog {} by user {}.".format(
        new_user.for_log,
        blog.for_log,
        user.for_log))

def create_user_site(**new_user_data):

    new_user = user_create(**new_user_data)
    site = new_user_data['site']

    saved_permission = add_user_permission(new_user,
         permission=127,
         site=site)

    user = user_from_ka(**new_user_data)

    logger.info("User {} created on site {} by user {}.".format(
        new_user.for_log,
        site.for_log,
        user.for_log))

def update_user(user, editing_user, **user_data):

    user.name = user_data['name']
    user.email = user_data['email']

    user.save()

    logger.info("Changes to user {} saved by user {}.".format(
        user.for_log,
        editing_user.for_log))

    return user

# TODO: move this into the User object schema itself?
def add_user_permission(user, **permission):

    new_permission = Permission()
    new_permission.user = user
    new_permission.permission = permission['permission']
    new_permission.site = permission['site']

    try:
        new_permission.blog = permission['blog']
    except KeyError:
        pass

    new_permission.save()

    return new_permission
