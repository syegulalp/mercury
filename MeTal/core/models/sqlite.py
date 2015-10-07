import os
import settings
from core.models import init_db, db
from core.models import Page, TextField, get_site
from core.libs.peewee import OperationalError
from core.libs import bottle
_stderr = bottle._stderr

try:
    from core.libs.playhouse.sqlite_ext import FTSModel

    class Page_Search(FTSModel):
        title = TextField()
        text = TextField()
        class Meta:
            database = db
except:
    raise

def db_is_locked():
    return "database is locked"

def recreate_database():

    db.close()

    try:
        os.remove(settings.FULL_SQLITE_DATABASE_PATH)
    except OSError as e:
        from core.error import not_found
        if not_found(e) is False:
            raise e
    except Exception as e:
        raise e

    try:
        os.mkdir(settings.APPLICATION_PATH + settings._sep + settings.DATA_FILE_PATH)
    except OSError as e:
        from core.error import file_exists
        if file_exists(e) is False:
            raise e
    except Exception as e:
        raise e

    init_db.recreate_database()

def clean_database():
    recreate_database()
    remove_indexes()

def make_db_connection():

    _stderr ("Looking for database in " + settings.DATABASE_PATH + "\n")

    if settings.RESET or not os.path.exists(settings.FULL_SQLITE_DATABASE_PATH):

        _stderr ("No database found or settings.RESET was set.\n")

        # db.close()
        # throws spurious AttributeError when no DB present

        from core.error import FileNotFoundError

        try:
            os.remove(settings.FULL_SQLITE_DATABASE_PATH)
        except FileNotFoundError:
            _stderr ("Database already removed.\n")
        else:
            _stderr ("Database removed.\n")
        finally:
            _stderr ("Re-initializing database.\n")

        init_db.recreate_database()

def create_index_table():
    _stderr ("Creating SQLite index tables.\n")
    try:
        Page_Search.create_table()
    except OperationalError:
        _stderr ("Could not add full-text indexes to this version of SQLite.\n")

def remove_indexes():
    _stderr ("Removing SQLite indexes.\n")
    try:
        Page_Search.drop_table()
    except BaseException:
        _stderr ("Could not remove indexes.\n")

def recreate_indexes():
    _stderr ("Recreating SQLite indexes.\n")
    Page_Search.create_table(content=Page)
    Page_Search.rebuild()
    Page_Search.optimize()

def site_search(search_terms_enc, site):
    ct = 0

    if site is not None:
        site_to_search = get_site(site).pages().select(Page.id).tuples()

    try:
        search_results = (Page_Search.select(Page_Search.id)
            .where(Page_Search.id << site_to_search,
                Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
            .order_by(Page_Search.id.desc()).tuples())
        ct = search_results.count()  # This statement is used to trap FTS4 errors
    except OperationalError:
        pass
    if ct == 0:
        search_results = (Page.select(Page.id)
            .where(Page.blog.site == site,
                Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
            .order_by(Page.id.desc()).tuples())

    return search_results

def blog_search(search_terms_enc, blog):

    ct = 0

    if blog is not None:
        blog_to_search = blog.pages().select(Page.id).tuples()

    try:
        search_results = (Page_Search.select(Page_Search.id)
            .where(Page_Search.id << blog_to_search,
                Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
            .order_by(Page_Search.id.desc()).tuples())
        ct = search_results.count()  # This statement is used to trap FTS4 errors
    except OperationalError:
        pass
    if ct == 0:
        search_results = (Page.select(Page.id)
            .where(Page.blog == blog,
                Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
            .order_by(Page.id.desc()).tuples())

    return search_results

def media_search():
    pass

def dataset_connection():
    return 'sqlite:///' + settings.DATABASE_PATH

def clear_table(*args):  # @UnusedVariable
    return ""

def set_table(*args):  # @UnusedVariable
    return ""

def pre_import():
    return ""

def post_import():
    return ""

def post_recreate():
    return ""

def db_warnings():
    from core.error import LoggedException
    return LoggedException, "{} ({})"
