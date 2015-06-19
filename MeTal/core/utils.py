import urllib, re, html

from settings import (MAX_BASENAME_LENGTH, ITEMS_PER_PAGE,
    PASSWORD_KEY, SECRET_KEY, BASE_URL, BASE_URL_ROOT)
 
from libs.bottle import template, redirect

import hashlib, base64

from libs.bottle import _stderr

def url_escape(url):
    return urllib.parse.quote_plus(url)

def url_unescape(url):
    return urllib.parse.unquote_plus(url)

def safe_redirect(url):
    url_unquoted = urllib.parse.unquote_plus(url)
    if url_unquoted.startswith(BASE_URL_ROOT + "/"):
        redirect(url)
    else:
        redirect(BASE_URL)
    
   
def _stddebug_():
    from core.boot import settings
    _stddebug = lambda x: _stderr(x) if (settings.DEBUG_MODE is True) else lambda x: None  # @UnusedVariable
    return _stddebug
    
class Status:
    '''
    Used to create status messages for AJAX UI.        
    '''
    def __init__(self, **ka):

        self.type = ka['type']
        if 'vals' in ka:
            formatting = list(map(html_escape, ka['vals']))
            self.message = ka['message'].format(*formatting)
        else:
            self.message = ka['message']

        if self.type == 'warning':
            self.icon = "warning-sign"
        else:
            self.icon = "info-sign"


def logout_nonce(user):
    
    return csrf_hash(str(user.id) + str(user.last_login) + 'LOGOUT')
    
def csrf_hash(csrf):
    '''
    Generates a CSRF token value, by taking an input and generating a SHA-256 hash from it,
    in conjunction with the secret key set for the installation.   
    '''
    
    enc = str(csrf) + SECRET_KEY
        
    m = hashlib.sha256()
    m.update(enc.encode('utf-8'))
    m = m.digest()
    encrypted_csrf = base64.b64encode(m).decode('utf-8')
    
    return (encrypted_csrf)

def csrf_tag(csrf):
    '''
    Generates a hidden input field used to carry the CSRF token for form submissions.  
    '''
    return "<input type='hidden' name='csrf' id='csrf' value='{}'>".format(csrf_hash(csrf)) 

def date_format(datetime):
    '''
    Formats a datetime value in a consistent way for presentation.
    '%Y-%m-%d %H:%M:%S' is the standard format. 
    '''
    if datetime is None:
        return ''
    else:
        return datetime.strftime('%Y-%m-%d %H:%M:%S')    
    

def utf8_escape(input_string):
    '''
    Used for cross-converting a string to encoded UTF8;
    for instance, for database submissions,
    '''
    return bytes(input_string, 'iso-8859-1').decode('utf-8')

def html_escape(input_string):
    '''
    Used for returning text from the server that might have HTML that needs escaping,
    such as a status message that might have spurious HTML in it (e.g., a page title).
    '''
    return html.escape(str(input_string))


def create_basename(input_string, blog):
    '''
    Generate a basename from a given input string.
    
    Checks across the entire blog in question for a basename collision.
    
    Basenames need to be unique to the filesystem for where the target files
    are to be written. By default this is enforced in the database by way of a
    unique column constraint.
    '''
    from models import Page
    
    if not input_string:
        input_string = "page"

    basename = input_string.replace(' ', '-')

    try:
        basename = basename.casefold()
    except BaseException:
        basename = basename.lower()
    
    basename = re.sub(r'[^a-z0-9\-]', r'', basename)
    basename = re.sub(r'\-\-', r'-', basename)
    basename = urllib.parse.quote_plus(basename)
    
    basename_test = basename
    
    n = 0
    
    while True:
        
        try:
            Page.get(Page.basename == basename_test,
                Page.blog == blog)
        except Page.DoesNotExist:
            return (basename_test[:MAX_BASENAME_LENGTH])

        n += 1
        basename_test = basename + "-" + str(n)

def trunc(string, length=128):
    '''
    Truncates a string with ellipses.
    This function may eventually be replaced with a CSS-based approach.
    '''
    if string is None:
        return ""
    string = (string[:length] + ' ...') if len(string) > length else string
    return string

def breaks(string):
    '''
    Used to break up URLs so that they break along /s
    '''
    string = string.replace('/', '/<wbr>')
    return string

def tpl(*args, **ka):
    '''
    Shim for the template function to force it to use a string that might be
    ambiguously a filename.
    '''
    # TODO: debug handler for errors in submitted user templates here?

    x = template("\n" + args[0], ka)
    return x[1:]

def generate_paginator(obj, request, items_per_page=ITEMS_PER_PAGE):

    '''
    Generates a paginator block for browsing lists, for instance in the blog or site view.
    '''
    page_num = page_list_id(request)
    
    paginator = {}
    
    paginator['page_count'] = obj.count()
    
    paginator['max_pages'] = int((paginator['page_count'] / items_per_page) + (paginator['page_count'] % items_per_page > 0))
    
    if page_num > paginator['max_pages']:
        page_num = paginator['max_pages']
    
    paginator['next_page'] = (page_num + 1) if page_num < paginator['max_pages'] else paginator['max_pages']
    paginator['prev_page'] = (page_num - 1) if page_num > 1 else 1
    
    paginator['first_item'] = (page_num * items_per_page) - (items_per_page - 1) 
    paginator['last_item'] = paginator['page_count'] if (page_num * items_per_page) > paginator['page_count'] else (page_num * items_per_page) 
    
    paginator['page_num'] = page_num
    paginator['items_per_page'] = items_per_page
    
    obj_list = obj.paginate(page_num, ITEMS_PER_PAGE)
    
    return paginator, obj_list

   

def generate_date_mapping(date_value, tags, path_string):
    '''
    Generates a date mapping string, usually from a template mapping,
    using a date value, a tag set, and the supplied path string.
    This is often used for resolving template mappings.
    The tag set is contextual -- e.g., for a blog or a site.
    '''
    
    time_string = date_value.strftime(path_string)
    path_string = tpl(time_string, **tags.__dict__)
    
    #path_string = path_string.replace('/', _sep)
    
    return path_string

    
def postpone(function):
    '''
    Thread launcher function
    '''
    def decorator(*args, **ka):
        t = Thread(target=function, args=args, kwargs=ka)
        t.daemon = True
        t.start()
        
    return decorator


def encrypt_password(password, key=None):
    
    if key is None:
        p_key = PASSWORD_KEY
    else:
        p_key = key
    
    bin_password = password.encode('utf-8')
    bin_salt = p_key.encode('utf-8')
    
    m = hashlib.sha256()
    for n in range(1, 1000):
        m.update(bin_password + bin_salt)
    m = m.digest()
    encrypted_password = base64.b64encode(m)
    
    return encrypted_password  

def memoize(f):
    '''
    Memoization decorator for a function taking one or more arguments.
    '''
    # pinched from http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
    class memodict(dict):
        def __getitem__(self, *key):
            return dict.__getitem__(self, key)
            
        def __missing__(self, key):
            ret = self[key] = f(*key)
            return ret
    
    return memodict().__getitem__

def memoize_delete(obj, item):
    obj.__self__.__delitem__(item) 
    
def _iter(item):
    try:
        (x for x in item)
    except BaseException:
        return (item,)
    else:
        return item


def page_list_id(request):
    
    if not request.query.page:
        return 1
    try:
        page = int(request.query.page)
    except ValueError:
        return 1
    return page