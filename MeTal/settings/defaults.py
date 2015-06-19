# Application install
# Do NOT change these settings! Use config.ini instead!
#####

# The encryption key for your logins.
# Change this after installation!
SECRET_KEY = "change_this_key_please"

# Key used for saving passwords in the db.
# DO NOT CHANGE THIS AFTER YOU HAVE CREATED YOUR USER ACCOUNTS!
PASSWORD_KEY = "also_change_this_key_please"

# The base URL for your MeTal installation.
# This should be the full URL to the folder
# where MeTal is installed, e.g.
# http://www.example.com/metal
BASE_URL_ROOT = "http://127.0.0.1"
BASE_URL_PATH = "/cms"

# Set this to True if you are running MeTal as an WSGI application,
# for instance on a shared webhost.
# Desktop mode overrides this to False. 
USE_WSGI = True


# Set this to True when you are using the program
# on your own desktop PC.
DESKTOP_MODE = False
#DESKTOP_MODE = True

# Debug mode. Set to True for more detailed error messages.
# Don't set this to True in production unless you know what you're doing.
DEBUG_MODE = False

# Set to True if you want a browser window to come up automatically
# when running in desktop mode.
LAUNCH_BROWSER = False

# Set this to True to perform a factory reset to the default settings.
# ? to be phased out and replaced with a command line setting?
RESET = None

# Default port for when running in desktop mode.
# You generally don't need to change this unless
# another application is using it.
DEFAULT_LOCAL_PORT = "8080"
DEFAULT_LOCAL_ADDRESS = "127.0.0.1"
MAX_BASENAME_LENGTH = 128

# Number of operations to be performed from the queue in a single batch.
# You can set this to a higher value on systems where you aren't worried
# about batch operations timing out, but the default should suffice.
MAX_BATCH_OPS = 100

# Number of items listed on a page in a listing view.
ITEMS_PER_PAGE = 15

# For MySQL compatibility. Do not change.
ENFORCED_CHARFIELD_CONSTRAINT = 767

MAX_FILESIZE = 300000

INSTALL_STEP = None

INI_FILE_NAME = 'config.ini'

DAYS_TO_KEEP_LOGS = 30


# if desktop mode on install...
# if WSGI


# TODO: we may need to put in another test here for desktop mode on install
# or move these checks into the actuall install routine so they aren't
# constantly being hit here

#####
# Apply settings from config.ini to these install

import os
_sep = os.sep

APPLICATION_PATH = (os.path.dirname(os.path.realpath(__file__))).rpartition(_sep)[0]

from configparser import ConfigParser

config_file = APPLICATION_PATH + os.sep + 'data' + os.sep + INI_FILE_NAME

parser = ConfigParser()
parser.read(config_file)

if len(parser.sections()) == 0:
    NO_SETUP = True
else:
    NO_SETUP = False

    for items in parser.sections():
        for name, value in parser.items(items):
            option = name.upper()
            if value in ('True','False','None'):
                locals()[option]=parser.getboolean(items, option)
            else:
                locals()[option]=value
            
if INSTALL_STEP is not None:
    NO_SETUP = True 
# detect setup in progress here