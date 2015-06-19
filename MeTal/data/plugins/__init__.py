from functools import wraps
from settings import PLUGIN_PATH, DEBUG_MODE, PLUGIN_FILE_PATH, BASE_PATH, _sep
import os, importlib

from libs import bottle
_stderr = bottle._stderr

from core.error import PluginImportError

from models import Plugin, db

# eventually make this our standard interface for plugins
class _Plugin():
    pass

def plugin_before(plugin_function):

    def decorate(func):
    
        @wraps(func)
        def wrapper(*args, **ka):

            newargs, newka = plugin_function(*args, **ka)
            result = func(*newargs, **newka)
            return result
            
        return wrapper
       
    return decorate

def plugin_after(plugin_function):

    def decorate(func):
    
        @wraps(func)
        def wrapper(*args, **ka):

            initial_result = func(*args, **ka)
            result = plugin_function(initial_result) 

            return result
            
        return wrapper
       
    return decorate

def register_plugin(path_to_plugin):
    # Adds a plugin to the list of available plugins in the system registry
    # Plugins are not automatically registered
    if os.path.isfile(PLUGIN_PATH + _sep + path_to_plugin + _sep + "__init__.py"):
        
        try:
            added_plugin = importlib.import_module("plugins." + path_to_plugin)
        except SystemError:
            raise PluginImportError("Plugin at " + PLUGIN_PATH + _sep + path_to_plugin + " could not be registered.")
        else:
            
            try:
                existing_plugin = Plugin.select().where(
                    Plugin.path == path_to_plugin).get()
            except:
                        
                new_plugin = Plugin(
                    # TODO: use path, not short_name
                    name=added_plugin.__short_name__,
                    friendly_name=added_plugin.__plugin_name__,
                    path=path_to_plugin,
                    priority=1,
                    enabled=True)
                new_plugin.save()
                
                if DEBUG_MODE:
                    _stderr ("Plugin registered: " + added_plugin.__plugin_name__ + "\n")
                    
                return new_plugin
            
            else:
                raise PluginImportError("Plugin at " + PLUGIN_FILE_PATH + "/" + path_to_plugin + " is already registered.")

# eventually we will iterate through the list of registered plugins, not the directory
# and load them in the specified order, too

plugin_attributes = (
    '__plugin_name__',
    '__short_name__',
    '__plugin_description__',
    '__author__',
    '__version__',
    'load'
    )
    
# to verify:
# assert 'x' in x.__dict__

plugin_list = {}
    
def activate_plugins():
    
    #from data.plugins.minify import load 
    
    from core.utils import _stddebug_
    _stddebug = _stddebug_()
    
    _stddebug("Activating plugins.\n")

    plugin_errors = []
    
    plugins_to_activate = Plugin.select().where(Plugin.enabled == True)
    
    
    
    for n in plugins_to_activate:
        
        try:
            added_plugin = importlib.import_module("."+n.path,package='data.plugins')
        except ImportError as e:
            plugin_errors.append("\nPlugin " + n.friendly_name + " could not be activated. The path '" + PLUGIN_FILE_PATH + _sep + n.path + "' may be wrong. ({})".format(str(e)))
            continue
        except SystemError:
            plugin_errors.append("\nPlugin at '" + PLUGIN_FILE_PATH + _sep + n.path + "' could not be activated. The plugin may be improperly installed.")
            continue
        
        # we may want to move this test below into the import function
        # the full range of checks should be performed there to keep things from being slowed down
        
        try:
            for m in plugin_attributes:
                p_a = added_plugin.__getattribute__(m)
            
        except AttributeError:
            plugin_errors.append("\nPlugin at '" + PLUGIN_FILE_PATH + _sep + n.path + "' is missing one or more of its configuration attributes. The plugin may be damaged or improperly installed.")
            continue
        
        _stddebug("Plugin activated: " + added_plugin.__plugin_name__ + "\n")
            
        plugin_list[added_plugin.__short_name__] = added_plugin
        
        try:
            added_plugin.load()
        except BaseException as e:
            raise e
    
    if len(plugin_errors) > 0:
        raise PluginImportError(''.join(plugin_errors))
    
    _stddebug("\n")
        

def enable_plugin(plugin_id):     
    with db.atomic():
        try:
            plugin_to_enable = Plugin.select().where(Plugin.id == plugin_id).get()
        except BaseException:
            raise ("Plugin not found")
        else:
            if plugin_to_enable.enabled is True:
                bottle.redirect(BASE_PATH + "/system/plugins")
            else:
                plugin_to_enable.enabled = True
                plugin_to_enable.save()
    from core.boot import reboot
    reboot()
            
def disable_plugin(plugin_id):
    with db.atomic():
        try:
            plugin_to_disable = Plugin.select().where(Plugin.id == plugin_id).get()
        except BaseException:
            raise ("Plugin not found")
        else:
            if plugin_to_disable.enabled is False:
                bottle.redirect(BASE_PATH + "/system/plugins")
            else:
                plugin_to_disable.enabled = False
                plugin_to_disable.save()
    from core.boot import reboot
    reboot() 