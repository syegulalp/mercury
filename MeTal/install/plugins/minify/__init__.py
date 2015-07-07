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
    
    from core import cms
    from plugins import plugin_after
    from .minify import minify
    
    cms.generate_page_text = plugin_after(minify)(cms.generate_page_text)
    
def uninstall():
    pass
