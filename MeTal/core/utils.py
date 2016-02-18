import urllib, re, html

from settings import (MAX_BASENAME_LENGTH, ITEMS_PER_PAGE,
    PASSWORD_KEY, SECRET_KEY, BASE_URL, BASE_URL_ROOT)

from core.libs.bottle import redirect, response

import hashlib, base64

from core.libs.bottle import _stderr

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def default(obj):
    import datetime
    if isinstance(obj, datetime.datetime):
        return datetime.datetime.strftime(obj, '%Y-%m-%d %H:%M:%S')

def json_dump(obj):
    import json
    from core.libs.playhouse.shortcuts import model_to_dict
    # we have to do this as a way to keep dates from choking
    return json.loads(json.dumps(model_to_dict(obj, recurse=False),
            default=default,
            separators=(', ', ': '),
            indent=1))

def field_error(e):
    _ = re.compile('UNIQUE constraint failed: (.*)$')
    m = _.match(str(e))
    error = {'blog.local_path':'''
The file path for this blog is the same as another blog in this system.
File paths must be unique.
''', 'blog.url':'''
The URL for this blog is the same as another blog in this system.
URLs for blogs must be unique.
'''}[m.group(1)]
    return error

def quote_escape(string):
    string = string.replace("'", "&#39")
    string = string.replace('"', "&#34")
    return string

def preview_file(identifier, extension):
    file_identifier = "preview-{}".format(identifier)
    import zlib
    return ('preview-' +
        str(zlib.crc32(file_identifier.encode('utf-8'), 0xFFFF)) +
        "." + extension)

def preview_file_old(filename, extension):
    import zlib
    try:
        split_path = filename.rsplit('/', 1)[1]
    except IndexError:
        split_path = filename
    return ('preview-' +
        str(zlib.crc32(split_path.encode('utf-8'), 0xFFFF)) +
        "." + extension)

def verify_path(path):
    '''
    Stub function to ensure a given path
    a) exists
    b) is writable
    c) is not on top of a path used by the application
    '''

    # verify the path exists
    # verify that it is writable
    # verify it is not within the application directory

    pass

def is_blank(string):
    if string and string.strip():
        return False
    return True

def url_escape(url):
    return urllib.parse.quote_plus(url)

def url_unescape(url):
    return urllib.parse.unquote_plus(url)

def safe_redirect(url):
    url_unquoted = urllib.parse.unquote_plus(url)
    if url_unquoted.startswith(BASE_URL + "/"):
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
    status_types = {'success':'ok-sign',
        'info':'info-sign',
        'warning':'exclamation-sign',
        'danger':'remove-sign'}

    def __init__(self, **ka):

        self.type = ka['type']
        if 'vals' in ka:
            formatting = list(map(html_escape, ka['vals']))
            self.message = ka['message'].format(*formatting)
        else:
            self.message = ka['message']

        if self.type not in ('success', 'info') and 'no_sure' not in ka:
            self.message += "<p><b>Are you sure you want to do this?</b></p>"


        if self.type in self.status_types:
            self.icon = self.status_types[self.type]

        self.confirm = ka.get('yes', None)
        self.deny = ka.get('no', None)

        self.action = ka.get('action', None)
        self.url = ka.get('url', None)

        self.message_list = ka.get('message_list', None)
        self.close = ka.get('close', True)


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

def string_to_date(date_string):
    import datetime
    return datetime.datetime.strptime(date_string, DATE_FORMAT)

def date_format(date_time):
    '''
    Formats a datetime value in a consistent way for presentation.
    '%Y-%m-%d %H:%M:%S' is the standard format.
    '''
    if date_time is None:
        return ''
    else:
        return date_time.strftime(DATE_FORMAT)


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

def create_basename_core(basename):
    try:
        basename = basename.casefold()
    except Exception:
        basename = basename.lower()

    basename = basename.replace(' ', '-')
    basename = re.sub(r'<[^>]*>', r'', basename)
    basename = re.sub(r'[^a-z0-9\-]', r'', basename)
    basename = re.sub(r'\-\-', r'-', basename)
    basename = urllib.parse.quote_plus(basename)

    return basename

def create_basename(input_string, blog):
    '''
    Generate a basename from a given input string.

    Checks across the entire blog in question for a basename collision.

    Basenames need to be unique to the filesystem for where the target files
    are to be written. By default this is enforced in the database by way of a
    unique column constraint.
    '''

    if not input_string:
        input_string = "page"

    basename = input_string
    basename_test = create_basename_core(basename)

    from core.models import Page

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

breaks_list = ['/', '.', '-', '_']

def breaks(string):
    '''
    Used to break up URLs and basenames so they wrap properly
    '''
    if string is None:
        return string

    for n in breaks_list:
        string = string.replace(n, n + '<wbr>')

    return string

def tpl_oneline(string):

    if string[0] == '%':
        string = '\\' + string

    return string

def tpl_include(tpl):
    # get absolute path for template relative to blog root
    # get default mapping
    # prepend /? do we need to have those in the mapping?
    return '<!--#include virtual="{}" -->'.format(
        tpl)

from core.libs.bottle import SimpleTemplate
class MetalTemplate(SimpleTemplate):
    includes = []
    def __init__(self, *args, **kwargs):
        super(MetalTemplate, self).__init__(*args, **kwargs)
        self._tags = kwargs.get('tags', None)

    def _include(self, env, _name=None, **kwargs):
        from core.models import Template
        template_to_import = Template.get(
            Template.blog == self._tags.get('blog', None),
            Template.title == _name)
        tpl = MetalTemplate(template_to_import.body, tags=self._tags)
        self.includes.append(_name)
        return tpl.execute(env['_stdout'], env)
    def render(self, *args, **kwargs):
        return super(MetalTemplate, self).render(*args, **kwargs)

def tpl(*args, **ka):
    '''
    Shim for the template function to force it to use a string that might be
    ambiguously a filename.
    '''
    # TODO: debug handler for errors in submitted user templates here?
    tp = MetalTemplate('\n' + args[0], tags=ka)
    x = tp.render(ka)
    return x[1:]

tp_cache = {}

def tpl2(template, **ka):
    try:
        template_to_render = tp_cache[template.blog.id][template.id]
    except KeyError:
        template_to_render = MetalTemplate('\n' + template.body, tags=ka)
        tp_cache[template.blog.id][template.id] = template_to_render
    x = template_to_render.render(ka)
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


def raise_request_limit():
    from core.libs import bottle
    import settings
    bottle.BaseRequest.MEMFILE_MAX = settings.MAX_REQUEST

def disable_protection():
    response.set_header('Frame-Options', '')
    # response.set_header('Content-Security-Policy', '')

def action_button(label, url):
    action = "<a href='{}'><button type='button' class='btn btn-sm'>{}</button></a>".format(
        url,
        label
        )

    return action
