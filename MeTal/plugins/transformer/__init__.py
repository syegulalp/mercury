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
    from core import cms
    from plugins import plugin_before
    from .transform import transform 

    cms.generate_page_text = plugin_before(transform)(cms.generate_page_text)
    
    '''alternate:
    have the loader do the actual wrapping
    return ('before',transform,'cms.generate_page_text')
    return ('before',transform,cms.generate_page_text)
    which would be more appropriate?
    i say, return a name and look that up
    make the loader do the checking?
    worth trying the easy way first maybe   
    
    '''    
    
    
# do we need this?
# why not just call plugin_list{}?
'''
def register():
    from .transform import transform
    return transform
'''