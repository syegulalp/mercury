__plugin_name__ = "Minify"
__short_name__ = "minify"
__plugin_description__ = "Minifies page output."
__author__ = 'Serdar Yegulalp'
__version__ = '0.1'
__license__ = 'MIT'
__compatibility__ = 0


def ui(plugin):
    d = plugin.data()
    settings = []
    for n in d:
        settings.append('{},{},{}'.format(n.key, n.text_value, n.int_value))
    return "Settings for plugin: {}. {} {}".format(plugin.description,
                                                   plugin.data().count(),
                                                '<p>'.join(settings))


def install():

    settings = (
        {
            'key':'remove_newlines',
            'int_value':1,
        },
        {
            'key':'remove_tabs',
            'int_value':1,
        },
        {
            'key':'whitelist',
            'text_value':'',
        }
        )

    return {'settings':settings}


def load():

    sidebar = {
        'add_to': 'edit_page',
        'panel': {
            'template': 'This is a test!\n',
            'title': 'Test',
            'label': 'test',
            'icon': 'picture'
        },

    }

    from .lib import minify

    return ({
            'action': 'before',
            'module': 'core.cms.queue',
            'function': 'write_file',
            'wrap': minify
            },
            {
            'action': 'exec',
            'module': 'core.ui.sidebar',
            'function': 'register_sidebar',
            'kwargs': sidebar
            })


def uninstall():
    pass
