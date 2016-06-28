import os, datetime, json
from settings import (APPLICATION_PATH, EXPORT_FILE_PATH, BASE_URL, DB, _sep)
from core.utils import Status, encrypt_password, is_blank
from core.log import logger
from core.models import (TemplateMapping, Template, System, KeyValue,
    Permission, Site, Blog, User, Category, Theme, Tag)
from core.libs.playhouse.dataset import DataSet
from os.path import join as _join
'''
def theme_apply_to_blog(theme, blog, user):

    from core import cms
    cms.purge_fileinfos(blog.fileinfos)
    blog.erase_theme()
    from settings import THEME_FILE_PATH

    theme_dir = _join(THEME_FILE_PATH, theme.json)

    for subdir, dirs, files in os.walk(theme_dir):
        for n in files:
            if n == '__manifest__.json':
                continue
            if n[-4:] == '.tpl':
                continue
            with open(_join(theme_dir, n), 'r', encoding='utf8') as f:
                template = json.loads(f.read())
                tpl_data = template['template']
                with open(_join(theme_dir, n[:-5] + '.tpl'), 'r', encoding='utf8') as b:
                    tpl_data['body'] = b.read()

                mapping_data = template['mappings']

                table_obj = Template()

                for name in table_obj._meta.fields:
                    if name not in ('id', 'blog', 'template_ref'):
                        setattr(table_obj, name, tpl_data[name])

                table_obj.template_ref = n
                table_obj.blog = blog
                table_obj.theme = theme
                table_obj.save(user)

                for mapping in mapping_data:
                    mapping_obj = TemplateMapping()
                    for name in mapping_obj._meta.fields:
                        if name not in ('id', 'template'):
                            setattr(mapping_obj, name, mapping_data[mapping][name])

                    mapping_obj.template = table_obj.id
                    mapping_obj.save()


    set_theme = Template.update(theme=theme).where(Template.theme == blog.theme)
    set_theme.execute()

    blog.theme = theme
    blog.theme_modified = False
    blog.save()

    cms.purge_blog(blog)

    return


def theme_install_to_system(theme_path):

    from settings import THEME_FILE_PATH

    # theme_dir = THEME_FILE_PATH + _sep + theme_path
    theme_dir = _join(THEME_FILE_PATH, theme_path)

    with open(_join(theme_dir, '__manifest__.json'), 'r') as f:
        json_data = f.read()

    json_obj = json.loads(json_data)

    new_theme = Theme(
        title=json_obj["title"],
        description=json_obj["description"],
        json=theme_path
        )

    new_theme.save()
    return new_theme
'''

def export_data():
    n = ("Beginning export process. Writing files to {}.".format(APPLICATION_PATH + EXPORT_FILE_PATH))
    yield ("<p>" + n)
    db = DataSet(DB.dataset_connection())
    if os.path.isdir(APPLICATION_PATH + EXPORT_FILE_PATH) is False:
        os.makedirs(APPLICATION_PATH + EXPORT_FILE_PATH)
    with db.transaction() as txn:
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

    # TODO: export n rows at a time from each table into a separate file
    # to make the import process more granular
    # by way of a query:
    # peewee_users = db['user'].find(favorite_orm='peewee')
    # db.freeze(peewee_users, format='json', filename='peewee_users.json')

def import_data():
    n = ("Beginning import process.")
    yield "<p>" + n

    n = ("Cleaning DB.")
    yield "<p>" + n
    try:
        DB.clean_database()
    except:
        from core.models import init_db
        init_db.recreate_database()
        DB.remove_indexes()

    n = ("Clearing tables.")
    yield "<p>" + n

    xdb = DataSet(DB.dataset_connection())

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
                    try:
                        table.thaw(format='json',
                            filename=filename,
                            strict=True)
                    except Exception as e:
                        yield("<p>Sorry, error:{}".format(e))

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
