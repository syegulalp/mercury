"""
import os, datetime, json
from settings import (APPLICATION_PATH, EXPORT_FILE_PATH, BASE_URL, DB, _sep)
from core.utils import Status, encrypt_password, is_blank
from core.log import logger
# from core.models import (TemplateMapping, Template, System, KeyValue,
    # Permission, Site, Blog, User, Category, Theme, Tag)
from core.libs.playhouse.dataset import DataSet
from os.path import join as _join

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

"""