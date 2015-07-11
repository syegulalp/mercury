__plugin_name__ = "Transformer"
__short_name__ = "transformer"
__plugin_description__ = "Uses regular expressions to transform contents of posts when published."
__author__ = 'Serdar Yegulalp'
__version__ = '0.1'
__license__ = 'MIT'
__compatibility__ = 0

def install():
    pass

def uninstall():
    pass

def load():
    from .lib import transform 

    return {'before':
        ('core.cms', 'generate_page_text', transform)
        }
