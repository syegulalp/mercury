from core import (auth, utils)
from core.cms.queue import job_type
from core.menu import generate_menu, colsets
# from core.search import site_search_results

from core.models import (
    template_tags, Queue, Log, Blog, Site,
    Plugin)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)
from . import search_contexts, listing

@transaction
def system_info():

    # alt. implementation, less boilerplate?
    # user, permission = auth.is_sys_admin()

    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    tags = template_tags(
        user=user)

    python_list = []
    environ_list = []
    settings_list = []

    # Generate interpreter info
    import os
    data = os.environ.__dict__['_data']
    for n in data:
        environ_list.append((n, data[n]))

    # List all settings variables
    import settings
    s_dict = settings.__dict__
    for n in s_dict:
        if n is not '__builtins__':
            settings_list.append((n, s_dict[n]))

    # List all plugins

    tpl = template('ui/ui_system_info',
        menu=generate_menu('system_info', None),
        search_context=(search_contexts['sites'], None),
        environ_list=sorted(environ_list),
        settings_list=sorted(settings_list),
        **tags.__dict__)

    return tpl

@transaction
def system_sites(errormsg=None):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    return listing(request, None, Site.select(),
                   'all_sites', 'manage_sites',
                   user=user)

@transaction
def system_queue():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    queue = Queue.select().order_by(Queue.site.asc(), Queue.blog.asc(), Queue.job_type.asc(),
        Queue.date_touched.desc())

    return listing(request, None, queue,
               'queue', 'system_queue',
               user=user)

@transaction
def system_log():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    log = Log.select().order_by(Log.date.desc(), Log.id.desc())

    return listing(request, None, log,
               'system_log', 'system_log',
               user=user)

@transaction
def register_plugin(plugin_path):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    from core.plugins import register_plugin, PluginImportError
    try:
        new_plugin = register_plugin(plugin_path)
    except PluginImportError as e:
        return (str(e))
    return ("Plugin " + new_plugin.friendly_name + " registered.")

@transaction
def plugin_settings(plugin_id, errormsg=None):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    plugin = Plugin.get(Plugin.id == plugin_id)

    tags = template_tags(
        user=user)

    tpl = template('system/plugin',
        plugin_ui=plugin.ui(),
        search_context=(search_contexts['sites'], None),
        menu=generate_menu('system_plugin_data', plugin),
        **tags.__dict__)

    return tpl

@transaction
def system_plugins(errormsg=None):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    plugins = Plugin.select()

    return listing(request, None, plugins,
                   'plugins', 'system_plugins',
                   user=user)

@transaction
def system_theme_data(theme_id):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    from core.models import Theme
    theme = Theme.load(theme_id)

    tags = template_tags(user=user)

    report = ['Theme title: {}'.format(theme.title),
        'Theme description: {}'.format(theme.description),
        'Theme directory: {}'.format(theme.json),
        '<hr>'
        ]

    tpl = template('listing/report',
        search_context=(search_contexts['sites'], None),
        menu=generate_menu('system_theme_data', theme),
        report=report,
        **tags.__dict__)

    return tpl

@transaction
def system_list_themes():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    from core.models import Theme

    return listing(request, None, Theme.select().order_by(Theme.id),
                   'themes_site', 'system_manage_themes',
                   user=user,
                   )


@transaction
def system_delete_theme(theme_id):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    # TODO: attach an installing user to the theme
    # allow that user to delete

    tags = template_tags(user=user)
    from core.models import Theme
    from settings import BASE_URL
    from core.utils import Status

    theme = Theme.load(theme_id)

    if request.forms.getunicode('confirm') == user.logout_nonce:

        from settings import THEME_FILE_PATH  # , _sep
        import shutil, os
        shutil.rmtree(os.path.join(THEME_FILE_PATH, theme.json))

        theme.delete_instance()

        status = Status(
            type='success',
            close=False,
            message='''
Theme <b>{}</b> was successfully deleted from the system.</p>
'''.format(theme.for_log),
            action='Return to theme list',
            url='{}/system/themes'.format(
                BASE_URL)
)

    else:

        m1 = '''You are about to remove theme <b>{}</b>. <b>THIS ACTION CANNOT BE UNDONE.</b></p>
'''.format(theme.for_display)
        blogs_with_theme = Blog.select().where(
            Blog.theme == theme_id)
        if blogs_with_theme.count() > 0:
            used_in = []
            for n in blogs_with_theme:
                used_in.append("<li>{}</li>".format(n.for_display))
            m2 = '''<p>This theme is in use by the following blogs:<ul>{}</ul>
Deleting this theme may <i>break these blogs entirely!</i></p>
'''.format(
                ''.join(used_in))
        else:
            m2 = ''

        status = Status(
            type='warning',
            close=False,
            message=m1 + m2,
            url='{}/system/theme/{}/delete'.format(
                BASE_URL, theme.id),
            yes={'id':'delete',
                'name':'confirm',
                'label':'Yes, I want to delete this theme',
                'value':user.logout_nonce},
            no={'label':'No, don\'t delete this theme',
                'url':'{}/system/themes'.format(
                BASE_URL)}
            )

    tags.status = status

    tpl = template('listing/report',
        menu=generate_menu('system_delete_theme', theme),
        search_context=(search_contexts['sites'], None),
        msg_float=False,
        **tags.__dict__)

    return tpl
