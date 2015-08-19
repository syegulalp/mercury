__plugin_name__ = "Minify"
__short_name__ = "minify"
__plugin_description__ = "Minifies page output."
__author__ = 'Serdar Yegulalp'
__version__ = '0.1'
__license__ = 'MIT'
__compatibility__ = 0


def install():
    pass

def load():

    sidebar = {
            'add_to':'edit_page',
            'panel':{
                'template':'\nThis is a test!',
                'title':'Test',
                'label':'test',
                'icon':'picture'
                },

            }

    from .lib import minify

    return ({
            'action':'after',
            'module':'core.cms',
            'function':'generate_page_text',
            'wrap':minify
        },
        {
            'action':'exec',
            'module':'core.ui_mgr',
            'function':'register_sidebar',
            'data':sidebar
            })

def uninstall():
    pass
