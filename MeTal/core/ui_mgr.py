from core.libs.bottle import template

# TODO: use this ordering mechanism elsewhere, too?

panels_dict = {
    'edit_template':
        {'panel_order':['publishing'],
        'panels':
            {'publishing':{
                'template':'sidebar_template_publishing_ui',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'}
            }
        },
    'edit_page':
        {'panel_order':['publishing', 'status', 'categories', 'tags', 'media', 'kv'],
        'panels':
            {'publishing':{
                'template':'sidebar_page_publishing_ui',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'
                },
            'status':{
                'template':'sidebar_page_status_ui',
                'title':'Page status',
                'label':'status',
                'icon':'info-sign'
                },
            'categories':{
                'template':'sidebar_page_categories_ui',
                'title':'Categories',
                'label':'categories',
                'icon':'th-list'
                },
            'tags':{
                'template':'sidebar_page_tags_ui',
                'title':'Tags',
                'label':'tags',
                'icon':'tags'
                },
            'kv':{
                'template':'sidebar_page_kv_ui',
                'title':'Key/Value',
                'label':'kv',
                'icon':'tasks'
                },
            'media':{
                'template':'sidebar_page_media_ui',
                'title':'Media',
                'label':'media',
                'icon':'picture'
                }                
            }
        }
    }


def render_sidebar(**k):
    
    panels = panels_dict[k['panel_set']]['panel_order']
    panel_set = panels_dict[k['panel_set']]['panels'] 
    sidebar_panels = []
    
    for n in panels:
        panels_n = panel_set[n]
        if not 'collapse' in panels_n:
            panels_n['collapse'] = ''
        panel_body = template(panels_n['template'], **k)
        panel = template('sidebar_panel_ui',
            body=panel_body,
            **panels_n)         
        sidebar_panels.append(panel)
        
    sidebar_template = template('sidebar_ui', panels=''.join(sidebar_panels))
    
    return sidebar_template

def register_sidebar():
    '''
    Inputs are assumed to be unsafe.
    '''
    pass
