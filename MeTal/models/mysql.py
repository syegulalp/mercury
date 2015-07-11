import settings
from core.libs import bottle
_stderr = bottle._stderr
from models import Page

def make_db_connection():
    _stderr ("Using MySQL database: {}\n".format(settings.DB_ID))
    if settings.RESET:
        recreate_database()
        
def recreate_database():
    from models import init_db
    init_db.recreate_database()
    
def create_index_table():
    pass

def remove_indexes():
    pass

def recreate_indexes():
    pass

def clean_database():
    pass

def dataset_connection():
    dataset_connection = 'mysql://{}:{}@{}:{}/{}'.format(
        settings.DB_USER,
        settings.DB_PASSWORD,
        settings.DB_ADDRESS,
        settings.DB_PORT,
        settings.DB_ID)
    return dataset_connection 

def pre_import():
    return '''
SET FOREIGN_KEY_CHECKS = 0, UNIQUE_CHECKS=0, AUTOCOMMIT=0;
'''

def post_import():
    return '''
SET FOREIGN_KEY_CHECKS = 1, UNIQUE_CHECKS=1; COMMIT;
'''

def clear_table(table_name):
    #return "TRUNCATE TABLE `{}`;".format(table_name); 
    #return "ALTER TABLE `{}` DISABLE KEYS;".format(table_name, table_name);
    #return "ALTER TABLE `{}` DISABLE KEYS; TRUNCATE TABLE `{}`; ".format(table_name, table_name);
    return ""
    
def set_table(table_name):
    return ""
    #return "ALTER TABLE `{}` ENABLE KEYS; ".format(table_name);
    

def post_recreate():
    return '''
ALTER TABLE `page` ADD FULLTEXT INDEX `page_title` (`title`);
ALTER TABLE `page` ADD FULLTEXT INDEX `page_text` (`text`);
'''

def site_search(search_terms_enc):
    
    return (Page.select(Page.id)
        .where(Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
        .order_by(Page.id.desc()).tuples())
    
def blog_search(search_terms_enc):
    
    return (Page.select(Page.id)
        .where(Page.title.contains(search_terms_enc) | Page.text.contains(search_terms_enc))
        .order_by(Page.id.desc()).tuples())
    
def media_search():
    pass        


def db_warnings():
    import warnings
    warnings.filterwarnings("error", "Data truncated *")
    from core.libs.pymysql import MySQLError
    DBError = MySQLError
    error_text = "MySQL error: {} ({})"
    return DBError, error_text