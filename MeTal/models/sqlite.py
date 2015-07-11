import os
import settings
from models import init_db,db
from models import Page, TextField
from core.libs import bottle
from core.error import LoggedException
from core.libs.peewee import OperationalError
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
# would it be possible to just proxy PageSearch to Page?

def recreate_database():
    
    db.close()
    
    try:
        os.remove(settings.FULL_SQLITE_DATABASE_PATH)
    except FileNotFoundError: pass
    
    try:
        os.mkdir(settings.APPLICATION_PATH+"/data")
    except FileExistsError: pass

    init_db.recreate_database()
    
def clean_database():
    recreate_database()
    remove_indexes()
    
def make_db_connection():
    
    _stderr ("Looking for database in " + settings.DATABASE_PATH + "\n")

    if settings.RESET or not os.path.exists(settings.FULL_SQLITE_DATABASE_PATH):

        _stderr ("No database found or settings.RESET was set.\n")
        
        #db.close()
        #throws spurious AttributeError when no DB present        
        
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
    
def site_search(search_terms_enc):
    try:
        search_results = (Page_Search.select(Page_Search.id)
            .where(Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
            .order_by(Page_Search.id.desc()).tuples())
        ct = search_results.count()
        # This statement is used to trap FTS4 errors
    except OperationalError:
        search_results = (Page.select(Page.id)
            .where(Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
            .order_by(Page.id.desc()).tuples())
    return search_results
    
def blog_search(search_terms_enc):
    try:
        search_results = (Page_Search.select(Page_Search.id)
            .where(Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
            .order_by(Page_Search.id.desc()).tuples())
        ct = search_results.count()
        # This statement is used to trap FTS4 errors
    except OperationalError:
        search_results = (Page.select(Page.id)
            .where(Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
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
    return LoggedException, "{} ({})"