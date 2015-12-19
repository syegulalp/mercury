from core import (auth, utils)
from core.cms import job_type
from core.menu import generate_menu, colsets
from core.search import site_search_results

from core.models import (
    template_tags, Queue, Log,
    Plugin)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)
from .ui import search_context

@transaction
def system_info():

    user = auth.is_logged_in(request)

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
        menu=generate_menu('system_plugin', plugin),
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

    list_actions = [
        ['Uninstall', '{}/api/1/uninstall-plugin'],
        ]

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['sites'], None),
        menu=generate_menu('system_plugins', None),
        rowset=rowset,
        colset=colsets['plugins'],
        # list_actions=list_actions,
        **tags.__dict__)

    return tpl

@transaction
def system_delete_theme(blog_id):
    pass
    # verify input
    # make sure this theme isn't attached to an existing blog
