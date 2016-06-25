from core import (auth, utils)
from core.cms import job_type
from core.menu import generate_menu, colsets
# from core.search import site_search_results

from core.models import (
    template_tags, Queue, Log, Blog, Site,
    Plugin)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)
from .ui import search_context
from . import listing

@transaction
def system_info():
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
        search_context=(search_context['sites'], None),
        environ_list=sorted(environ_list),
        settings_list=sorted(settings_list),
        **tags.__dict__)

    return tpl

@transaction
def system_sites(errormsg=None):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    return listing(
        request, user, errormsg,
        {
            'colset':'all_sites',
            'menu':'manage_sites',
            'search_ui':'sites',
            'search_object':None,
            'search_context':None,
            'item_list_object':Site.select(),
            # 'action_button':action,
            # 'list_actions':list_actions
        },
        {
            'status':errormsg}
        )


    """

    try:
        sites_searched, search = site_search_results(request)
    except (KeyError, ValueError):
        sites_searched, search = None, None

    tags = template_tags(
        user=user)

    if errormsg is not None:
        tags.status = errormsg

    taglist = tags.sites

    paginator, rowset = utils.generate_paginator(taglist, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['sites'], None),
        menu=generate_menu('manage_sites', None),
        rowset=rowset,
        colset=colsets['all_sites'],
        **tags.__dict__)

    return tpl
    """


@transaction
def system_queue():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    queue = Queue.select().order_by(Queue.site.asc(), Queue.blog.asc(), Queue.job_type.asc(),
        Queue.date_touched.desc())

    tags = template_tags(user=user)

    paginator, queue_list = utils.generate_paginator(queue, request)

    tpl = template('queue/queue_ui',
        queue_list=queue_list,
        paginator=paginator,
        job_type=job_type.description,
        menu=generate_menu('system_queue', None),
        search_context=(search_context['site_queue'], None),
        **tags.__dict__)

    return tpl

@transaction
def system_log():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    log = Log.select().order_by(Log.date.desc(), Log.id.desc())

    tags = template_tags(user=user)
    paginator, rowset = utils.generate_paginator(log, request)

    tpl = template('listing/listing_ui',
        rowset=rowset,
        colset=colsets['system_log'],
        paginator=paginator,
        menu=generate_menu('system_log', None),
        search_context=(search_context['system_log'], None),
        **tags.__dict__)

    return tpl

@transaction
def old_system_plugins():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    tags = template_tags(
        user=user)

    plugins = Plugin.select()

    tpl = template('ui/ui_plugins',
        menu=generate_menu('system_plugins', None),
        search_context=(search_context['sites'], None),
        plugins=plugins,
        **tags.__dict__)

    return tpl

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
        plugin=plugin,
        search_context=(search_context['sites'], None),
        menu=generate_menu('system_plugin_data', plugin),
        **tags.__dict__)

    return tpl

@transaction
def system_plugins(errormsg=None):
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)

    tags = template_tags(
        user=user)

    plugins = Plugin.select()

    paginator, rowset = utils.generate_paginator(plugins, request)

    tags.status = errormsg if errormsg is not None else None

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['sites'], None),
        menu=generate_menu('system_plugins', None),
        rowset=rowset,
        colset=colsets['plugins'],
        **tags.__dict__)

    return tpl

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
        search_context=(search_context['sites'], None),
        menu=generate_menu('system_theme_data', theme),
        report=report,
        **tags.__dict__)

    return tpl

@transaction
def system_list_themes():
    user = auth.is_logged_in(request)
    permission = auth.is_sys_admin(user)
    from core.models import Theme
    themes = Theme.select().order_by(Theme.id)

    tags = template_tags(user=user)

    paginator, rowset = utils.generate_paginator(themes, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['sites'], None),
        menu=generate_menu('system_manage_themes', None),
        rowset=rowset,
        colset=colsets['themes_site'],
        **tags.__dict__)

    return tpl

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

        from settings import THEME_FILE_PATH, _sep
        import shutil
        shutil.rmtree(THEME_FILE_PATH + _sep + theme.json)

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
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl
