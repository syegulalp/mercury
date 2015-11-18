# Application install defaults
# Do NOT change these settings directly when running the application!
# Place installation-specific settings in /data/config.cgi instead!

import os
_environ = os.environ
_sep = os.sep

# Default port for when running in desktop mode.
# You generally don't need to change this unless
# another application is using it.
DEFAULT_LOCAL_ADDRESS = "127.0.0.1"
DEFAULT_LOCAL_PORT = ":8080"
DEFAULT_URL_PATH = ""
DEFAULT_SCRIPT = 'index.cgi'

# Set this to True when you are using the program
# on your own desktop PC.
DESKTOP_MODE = False

# The encryption key for your logins.
# This temporary key is only used during the setup process.
SECRET_KEY = "change_this_key_please"

# Key used for saving passwords in the db.
# This temporary key is only used during the setup process.
PASSWORD_KEY = "also_change_this_key_please"

# Set this to True if you are running MeTal as an WSGI application,
# for instance on a shared webhost.
# Desktop mode overrides this to False.
USE_WSGI = True

# Debug mode. Set to True for more detailed error messages.
# Don't set this to True in production unless you know what you're doing.
DEBUG_MODE = False

# Set to True if you want a browser window to come up automatically
# when running in desktop mode.
LAUNCH_BROWSER = False

# Set this to True to perform a factory reset to the default settings.
# ? to be phased out and replaced with a command line setting?
RESET = None

# Set to True to place the system into maintenance mode.
# This forbids access to anyone who is not a sysadmin.
MAINTENANCE_MODE = False

INSTALL_STEP = None

INI_FILE_NAME = 'config.cgi'
INSTALL_INI_FILE_NAME = 'install.cgi'

# For MySQL compatibility. Do not change.
ENFORCED_CHARFIELD_CONSTRAINT = 767

# TODO: move these?
DAYS_TO_KEEP_LOGS = 30
MAX_FILESIZE = 300000
# Number of operations to be performed from the queue in a single batch.
# You can set this to a higher value on systems where you aren't worried
# about batch operations timing out, but the default should suffice.
MAX_BATCH_OPS = 50
# Number of items listed on a page in a listing view.
ITEMS_PER_PAGE = 15
# Maximum length of basenames for pages.
MAX_BASENAME_LENGTH = 128

DATABASE_TIMEOUT = 600000
DATABASE_RETRIES = 10
RETRY_INTERVAL = 1

APPLICATION_PATH = (os.path.dirname(os.path.realpath(__file__))).rpartition(_sep)[0]

VIEW_PATH = APPLICATION_PATH + _sep + 'core' + _sep + 'views'

MAX_REQUEST = 409600

INSTALL_SRC_PATH = 'install'

DEFAULT_THEME = 'Amano 2015'
