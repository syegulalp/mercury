#
# This file should not be edited unless you're a high roller
# or you know what you're doing.
# 

from libs.playhouse.sqlite_ext import SqliteExtDatabase, MySQLDatabase

import os
_sep = os.sep

from .defaults import *

__author__ = 'Serdar Yegulalp'
__version__ = '0.0.1'
__license__ = 'MIT'
__copyright_date__ = "2015"

PRODUCT_NAME = "MeTal " + __version__

# Relative path for static content used by MeTal itself.
# Leave this as-is for most functionality.

DATA_FILE_PATH = _sep + 'data'
EXPORT_FILE_PATH = DATA_FILE_PATH + _sep + 'saved'
PLUGIN_FILE_PATH = DATA_FILE_PATH + _sep + "plugins"

# Top-level path to the application.
# Automatically calculated; does not need to be changed.

BASE_URL = BASE_URL_ROOT + BASE_URL_PATH
PLUGIN_PATH = APPLICATION_PATH + PLUGIN_FILE_PATH
STATIC_FILE_PATH = APPLICATION_PATH + _sep + 'static'
STATIC_PATH = '/static'

# Database path for Sqlite. Leave this as it is
# unless you want the database in another directory.
SQLITE_FILE_NAME = 'my_database.db'
SQLITE_DATABASE_PATH = DATA_FILE_PATH + _sep + SQLITE_FILE_NAME 
FULL_SQLITE_DATABASE_PATH = APPLICATION_PATH + SQLITE_DATABASE_PATH
DATABASE_PATH = FULL_SQLITE_DATABASE_PATH

DEFAULT_LOCAL_PORT = ":" + DEFAULT_LOCAL_PORT

if DESKTOP_MODE is True:
    BASE_PATH = "/~"
    BASE_URL_ROOT = 'http://' + DEFAULT_LOCAL_ADDRESS + DEFAULT_LOCAL_PORT
    BASE_URL = BASE_URL_ROOT + BASE_PATH
    USE_WSGI = False
else:
    BASE_PATH = ""
    # BASE_URL = BASE_URL_ROOT + BASE_URL_PATH
    # BASE_URL = BASE_URL_ROOT + BASE_PATH
    # BASE_PATH = BASE_URL_PATH
    # BASE_URL = BASE_URL_ROOT + BASE_PATH
    # pass
    
try:
    DB_TYPE_NAME
except:
    DB_TYPE_NAME = 'sqlite'
    
if DB_TYPE_NAME == 'sqlite':
    DB_TYPE = SqliteExtDatabase(FULL_SQLITE_DATABASE_PATH, threadlocals=True)
    from models import sqlite
    DB = sqlite    

if DB_TYPE_NAME == 'mysql':
    DB_TYPE = MySQLDatabase(DB_ID, user=DB_USER, passwd=DB_PASSWORD)
    from models import mysql
    DB = mysql