from core.libs.bottle import (request, template, redirect)
from core.boot import settings as _s
_sep = _s._sep
import os, random, string

from configparser import ConfigParser, DuplicateSectionError
config_file_name = (_s.APPLICATION_PATH + _s.DATA_FILE_PATH +
    _sep + "install.ini")
parser = ConfigParser()

class SetupError(BaseException):
    pass

def generate_key(N):

    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(N))

def read_ini(p):

    try:
        with open(config_file_name, "r", encoding='utf-8') as input_file:
            p.read_file(input_file)
    except:
        return None

    return p

def get_ini(section, option):

    read_ini(parser)

    try:
        value = parser.get(section, option)
    except:
        value = None
    return value

def store_ini(section, setting, value):

    read_ini(parser)

    try:
        parser.add_section(section)
    except DuplicateSectionError:
        pass

    parser.set(section, setting, value)

    try:
        with open(config_file_name, "w", encoding='utf-8') as output_file:
            parser.write(output_file)
    except BaseException as e:
        raise SetupError(str(e.__class__.__name__) + ": " + str(e))

def step_0_pre():

    path_to_check = _s.APPLICATION_PATH + _s.DATA_FILE_PATH
    if os.path.isdir(path_to_check) is False:
        os.makedirs(path_to_check)

    with open(path_to_check + _sep + "__init__.py", "w", encoding='utf-8') as output_file:
        output_file.write('')

    store_ini('main', 'INSTALL_STEP', '0')
    store_ini('key', 'PASSWORD_KEY', generate_key(32))
    store_ini('key', 'SECRET_KEY', generate_key(32))

    return {}

def step_0_post():

    return {}

def step_1_pre():

    store_ini('main', 'INSTALL_STEP', '1')

    email = get_ini("user", "email")
    password = get_ini("user", "password")

    if email is None:
        email = ""

    if password is None:
        password = ""

    return {'email':email,
        'password':password,
        'password_confirm':password
        }


def step_1_post():
    step_error = []

    user_email = request.forms.getunicode('input_email')
    user_password = request.forms.getunicode('input_password')

    if user_email == "":
        step_error.append("You must provide a valid email address.")

    if user_password == "" or len(user_password) < 8:
        step_error.append ("Your password cannot be blank or less than eight characters.")

    from core.libs.bottle import touni

    existing_password = get_ini("main", "password")
    new_password = user_password

    if (existing_password == "" or
        existing_password != new_password):
        existing_password = new_password

    if existing_password != request.forms.getunicode('input_password_confirm'):
        step_error.append('Your password and password confirmation did not match.')

    if len(step_error) > 0:
        raise SetupError('\n'.join(step_error))

    store_ini("user", "password", touni(existing_password))
    store_ini("user", "email", user_email)
    store_ini('main', 'INSTALL_STEP', '2')

    return {}

def step_2_pre():

    domain = get_ini("path", "base_url_root")
    if domain is None:
        domain = "http://" + request.environ['HTTP_HOST']


    install_path = _s.APPLICATION_PATH
    blog_path = install_path.rsplit(_sep, 1)[0]
    cms_path = "/" + install_path.rsplit(_sep, 1)[1]

    return {'domain':domain,
        'install_path':install_path,
        'cms_path':cms_path,
        'blog_path':blog_path}

def step_2_post():

    domain = request.forms.getunicode('input_domain')
    install_path = request.forms.getunicode('install_path')
    blog_path = request.forms.getunicode('blog_path')
    cms_path = request.forms.getunicode('cms_path')

    store_ini('path', 'base_url_root', domain)
    store_ini('path', 'base_url_path', cms_path)
    store_ini('install', 'install_path', install_path)
    store_ini('install', 'blog_path', blog_path)

    store_ini('main', 'INSTALL_STEP', '3')

    return {}

def step_3_pre():

    return {'db_address':'localhost',
        'db_port':3306,
        'db_name':'mysql',
        'db_username':'',
        'db_password':''}


def step_3_post():

    database_type = request.forms.getunicode('dbtype')

    if database_type == 'sqlite':
        store_ini('db', 'db_type_name', 'sqlite')

    if database_type == 'mysql':
        store_ini('db', 'db_type_name', 'mysql')

    store_ini('main', 'INSTALL_STEP', '4')

    return {'dbtype', database_type}

def step_4_pre():

    if get_ini('main', 'DO_DB_CHECK') is None:
        store_ini('main', 'DO_DB_CHECK', 'Y')
        from core.boot import reboot
        reboot()

    report = []

    from core.models import db, Template
    try:
        db.connect()
    except:
        raise

    db.close()

    report.append("Database connection successful.")

    from settings import DB
    DB.recreate_database()

    report.append("Database tables created successfully.")

    username = "Administrator"
    email = get_ini("user", "email")
    password = get_ini("user", "password")
    blog_path = get_ini("install", "blog_path")

    from core.utils import encrypt_password
    p_key = get_ini('key', 'PASSWORD_KEY')
    password = encrypt_password(password, p_key)

    from core import mgmt

    db.connect()

    with db.atomic():

        from core.models import System
        system_ref = System()

        system_ref.add_kv(
            object='System',
            objectid=0,
            key='MaxPageRevisions',
            value=20,
            is_schema=True,
            is_unique=True)

        system_ref.add_kv(
            object='System',
            objectid=0,
            key='AutomaticallyReleaseLocksAfter',
            value=3600,
            is_schema=True,
            is_unique=True)

        new_site = mgmt.site_create(
            name="Your first site",
            description="The description for your first site.",
            url=get_ini('path', 'base_url_root'),
            path=blog_path)

        report.append("Initial site created successfully.")

        new_user = mgmt.user_create(
            name='Administrator',
            email=email,
            encrypted_password=password)

        new_user.save()

        from core.auth import role

        new_user_permissions = mgmt.add_user_permission(
            new_user,
            permission=role.SYS_ADMIN,
            site=new_site
            )

        new_user_permissions.save()

        report.append("Initial admin user created successfully.")

        install_directory = (_s.APPLICATION_PATH + _sep +
            _s.INSTALL_SRC_PATH)

        with open(install_directory + _sep + "themes" +
            _sep + _s.DEFAULT_THEME + _sep + "templates.json", "rb") as json_file:
                json_text = json_file.read()

        new_theme = mgmt.theme_install_to_system(json_text)

        report.append("Theme created and installed successfully to system.")

        new_blog = mgmt.blog_create(
            site=new_site,
            name="Your first blog",
            description="The description for your first blog.",
            url=new_site.url,
            path=new_site.path,
            theme=new_theme
            )

        report.append("Initial blog created successfully.")

        mgmt.theme_install_to_blog(new_theme, new_blog, new_user)

        report.append("Theme installed in new blog successfully.")

        plugindir = (_s.APPLICATION_PATH + _sep + 'data' +
            _sep + 'plugins')

        import shutil

        # TODO: warn on doing this?
        # this should only happen with a totally fresh install, not an upgrade

        if (os.path.isdir(plugindir)):
            shutil.rmtree(plugindir)

        shutil.copytree(install_directory + _sep + 'plugins',
            plugindir)

        from core import plugins

        for x in os.listdir(plugindir):
            if (os.path.isdir(plugindir + _sep + x) is True and
                x != '__pycache__'):
                plugins.register_plugin(x)

        # TODO: export installed theme to data directory in /themes
        # that should be part of the theme installation process itself.


    db.close()

    # raise

    output_file_name = (_s.APPLICATION_PATH + _s.DATA_FILE_PATH +
        _sep + "config.ini")

    config_parser = ConfigParser()

    sections = ('db', 'path', 'key')

    for s in sections:
        for name, value in parser.items(s):
            try:
                config_parser.add_section(s)
            except DuplicateSectionError:
                pass
            config_parser.set(s, name, value)

    if request.environ['HTTP_HOST'] == _s.DEFAULT_LOCAL_ADDRESS + _s.DEFAULT_LOCAL_PORT:
        config_parser.add_section('server')
        config_parser.set('server', 'DESKTOP_MODE', 'True')

    try:
        with open(output_file_name, "w", encoding='utf-8') as output_file:
            config_parser.write(output_file)
    except BaseException as e:
        raise SetupError(str(e.__class__.__name__) + ": " + str(e))

    try:
        os.remove(config_file_name)
    except OSError as e:
        from core.error import not_found
        not_found(e)

    finished = '''
    <p>Installation is complete.
    '''

    return {'report':report,
        'finished':finished}

def step_4_post():

    from core.boot import reboot
    reboot()

    # return {}

tpl = '''
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/jquery.min.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/bootstrap.min.js"></script>
% include('include/header_min.tpl')
<div class="container">
<h3>Welcome to {{settings.PRODUCT_NAME}}</h3>
<hr/>
{{!crumbs}}
% if error is not None:
<div class="alert alert-warning">
<b>Oops:</b> The system encountered an error during setup:<p><b>{{error}}</b></p>
<p>If you don't know what this means, contact your administrator.
</div>
% end

<h4>{{!title}}</h4>
{{!text}}
<hr/>
</div>
</body>
</html>

'''

crumb_template = '''
<ol class="breadcrumb">
{}
</ol>
'''

def button(step, next_action, error=None):


    if step > 0:
        previous = '''
<a href="{}/install/step-{}"><button type="button" class="btn">&lt;&lt; Go back</button></a>
'''.format(_s.BASE_URL_PATH, step - 1)
    else:
        previous = ""

    if next_action is not None:

        next_str = '''
<button action="submit" class="btn">Continue &gt;&gt;</button>
'''
    else:
        if error is None:
            next_str = '''
<a href="{}/install/step-{}"><button class="btn">Continue &gt;&gt;</button></a>
'''.format(_s.BASE_URL_PATH, step + 1)
        else:
            next_str = "<button class='btn btn-danger'>Fix the above error and click here to continue</button>"

    return "<hr/>" + previous + next_str

crumb_element_active = '''
<li class="active">{}</li>
'''

crumb_element_link = '''
<li><a href="{}/install/step-{}">{}</a></li>
'''

step_text = {

    0:{'pre-step':step_0_pre,
        'post-step':step_0_post,
        'next_action':None,
        'crumb':'Welcome',
        'title':'Welcome to the setup for <b>{}</b>!'.format(_s.PRODUCT_NAME),
        'text':'''
<p>To get your installation up and running, we'll need to gather some information from you.
<p>If at any time you need to go to an earlier step in this list, click on its title above.
{{!button}}
'''
        },

    1:{'pre-step':step_1_pre,
        'post-step':step_1_post,
        'next_action':1,
        'crumb':'Your information',
        'title':'Administrator email and password',
        'text':'''
<p>First, you'll need to provide a valid email address and a password.
This will be used to identify the administrator on this installation.
<p>Do <i>not</i> use the same password that you use to access the email account in question.
<hr>
<form action="{{form_action}}"  method="post" class="form-horizontal">
  <div class="form-group">
    <label for="input_email" class="col-sm-2 control-label">Email</label>
    <div class="col-sm-7">
      <input type="email" class="form-control" id="input_email" name="input_email" placeholder="Email"
      value="{{email}}">
    </div>
  </div>
  <div class="form-group">
    <label for="input_password" class="col-sm-2 control-label">Password</label>
    <div class="col-sm-7">
      <input type="password" class="form-control" id="input_password" name="input_password" placeholder="Password"
      value ="{{password}}">
    </div>
  </div>
  <div class="form-group">
    <label for="input_password_confirm" class="col-sm-2 control-label">Confirm password</label>
    <div class="col-sm-7">
      <input type="password" class="form-control" id="input_password_confirm" name="input_password_confirm" placeholder="Password"
      value ="{{password_confirm}}">
    </div>
  </div>
{{!button}}
</form>
'''
        },

    2:{'pre-step':step_2_pre,
        'post-step':step_2_post,
        'next_action':2,
        'crumb':'Directories',
        'title':'Installation directories and hostname',
        'text':'''
        <p>Next, you'll need to specify the following:
        <ul>
        <li><label for="input_domain">the domain name for the server where the application's files are,</a>
        <li><label for="install_path">the path on the server to those files,</a>
        <li><label for="blog_path">and the path on the server to where the files for your first
        blog are to be placed.</a>
        </ul>
        <p>We've made a best guess as to what these might be, so if you're not sure about what to do here,
        just press Continue. You can always change them later.
<form action="{{form_action}}"  method="post" class="form-horizontal">

  <div class="form-group">
    <label for="input_domain" class="col-sm-2 control-label">Domain name</label>
    <div class="col-sm-7">
      <input type="input" class="form-control" id="input_domain" name="input_domain" placeholder="http://www.example.com"
      value="{{domain}}">
    </div>
  </div>

    <div class="form-group">
    <label for="cms_path" class="col-sm-2 control-label">URL path to application</label>
    <div class="col-sm-7">
      <input type="input" class="form-control" id="cms_path" name="cms_path" placeholder="/cms (e.g., for http://www.example.com/cms)"
      value="{{cms_path}}">
    </div>
  </div>

  <div class="form-group">
    <label for="install_path" class="col-sm-2 control-label">Server installation path</label>
    <div class="col-sm-7">
      <input type="input" class="form-control" id="install_path" name="install_path" placeholder="e.g., /home/user/html"
      value="{{install_path}}">
    </div>
  </div>

  <div class="form-group">
    <label for="blog_path" class="col-sm-2 control-label">Path on disk for first site/blog</label>
    <div class="col-sm-7">
      <input type="input" class="form-control" id="blog_path" name="blog_path" placeholder="Path"
      value="{{blog_path}}">
    </div>
  </div>
{{!button}}
</form>'''},

    3:{'pre-step':step_3_pre,
        'post-step':step_3_post,
        'next_action':3,
        'crumb':'Database',
        'title':'Database',
        'text':'''
<p>Now you'll need to specify the database you'll be using to store the site's data.
<p>If you don't know what to do here, just hit Continue and a database will be configured automatically.</p>
<form action="{{form_action}}" method="post" class="form-horizontal">
    <div class="form-group">
        <label for='dbtype' class="col-sm-2 control-label">Database:</label>
        <div class="col-sm-7">
            <select class='form-control' id="dbtype" name='dbtype'>
              <option value="sqlite">SQLite</option>
              <option value="mysql">MySQL</option>
            </select>
        </div>
    </div>
    <div id="db_data" style="display:none">
        <div class="form-group">
            <label for="db_address" class="col-sm-2 control-label">MySQL address</label>
            <div class="col-sm-7">
                <input type="input" class="form-control" id="db_address" name="db_address" placeholder="IP address or hostname of database"
                value="{{db_address}}">
            </div>
        </div>
        <div class="form-group">
            <label for="db_port" class="col-sm-2 control-label">MySQL port</label>
            <div class="col-sm-7">
                <input type="input" class="form-control" id="db_port" name="db_port" placeholder="IP port for database"
                value="{{db_port}}">
            </div>
        </div>
        <div class="form-group">
            <label for="db_name" class="col-sm-2 control-label">Database name</label>
            <div class="col-sm-7">
                <input type="input" class="form-control" id="db_name" name="db_name" placeholder="Name of MySQL database"
                value="{{db_name}}">
            </div>
        </div>
        <div class="form-group">
            <label for="db_user" class="col-sm-2 control-label">MySQL username</label>
            <div class="col-sm-7">
                <input type="input" class="form-control" id="db_user" name="db_user" placeholder="User with privileges for the above table (NOT root!)"
                value ="{{db_username}}">
            </div>
        </div>
        <div class="form-group">
            <label for="db_password" class="col-sm-2 control-label">Password</label>
            <div class="col-sm-7">
            <input type="password" class="form-control" id="db_password" name="db_password" placeholder="Password for database user"
            value ="{{db_password}}">
            </div>
        </div>
    </div>
{{!button}}
</form>
<script>$('#dbtype').on('change',function(){
    if (this.value=='mysql'){
    $('#db_data').show();
    }
    else
    {$('#db_data').hide();}
});
</script>
'''},
    4:{'pre-step':step_4_pre,
        'post-step':step_4_post,
        'next_action':5,
        'crumb':'Installing',
        'title':'Now installing ...',
        'text':'''
<ul>
% for n in report:
<li>{{n}}
% end
</ul>
{{!finished}}
'''}
    }

def crumbs(step):

    crumbs = []

    m = 0
    while True:
        try:
            n = step_text[m]
        except KeyError:
            break

        if m > step:
            crumb = crumb_element_active.format(n['crumb'])
        else:
            crumb = crumb_element_link.format(_s.BASE_URL_PATH, m, n['crumb'])

        crumbs.append(crumb)
        m += 1

        # http://docs.quantifiedcode.com/python-code-patterns/readability/using_an_unpythonic_loop.html

    return crumb_template.format(''.join(crumbs))

def step(step):

    error_msg = None

    if request.method == "POST":

        try:
            results = step_text[step]['post-step']()
        except SetupError as e:
            results = step_text[step]['pre-step']()
            error_msg = e
        else:
            step += 1
            redirect('{}/install/step-{}'.format(_s.BASE_URL_PATH, step))

    else:
        try:
            results = step_text[step]['pre-step']()
        except SetupError as e:
            error_msg = e
            results = {}

    if error_msg is None:
        template_button = button(step, step_text[step]['next_action'])
    else:
        template_button = button(step, None, error_msg)

    return template(tpl,
        settings=_s,
        step=step,
        title=step_text[step]['title'],
        text=template(step_text[step]['text'],
            button=template_button,
            form_action='{}/install/step-{}'.format(_s.BASE_URL_PATH, step),
            **results),
        crumbs=crumbs(step),
        error=error_msg)
