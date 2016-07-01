panels_dict = {
    'edit_category':
        {'panel_order':['kv', ],
        'panels':
            {
            'kv':{
                'template':'sidebar/kv',
                'title':'Key/Value',
                'label':'kv',
                'icon':'tasks'
                }
            }
        },
    'edit_media':
        {'panel_order':['kv', ],
        'panels':
            {
            'kv':{
                'template':'sidebar/kv',
                'title':'Key/Value',
                'label':'kv',
                'icon':'tasks'
                }
            }
        },
    'edit_template':
        {'panel_order':['publishing', 'status', 'files', 'theme'],
        'panels':
            {'publishing':{
                'template':'sidebar/template_publishing',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'},
            'status':{
                'template':'sidebar/template_status',
                'title':'Status',
                'label':'status',
                'icon':'info-sign'
                },
            'theme':{
                'template':'sidebar/template_theme',
                'title':'Theme',
                'label':'theme',
                'icon':'file'
                },
            'files':{
                'template':'sidebar/template_output',
                'title':'Output files',
                'label':'output',
                'icon':'file'
                }
            }
        },
    'edit_page':
        {'panel_order':['publishing', 'status', 'categories', 'tags', 'media', 'kv'],
        'panels':
            {'publishing':{
                'template':'sidebar/page_publishing',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'
                },
            'status':{
                'template':'sidebar/page_status',
                'title':'Page status',
                'label':'status',
                'icon':'info-sign'
                },
            'categories':{
                'template':'sidebar/page_categories',
                'title':'Categories',
                'label':'categories',
                'icon':'th-list'
                },
            'tags':{
                'template':'sidebar/page_tags',
                'title':'Tags',
                'label':'tags',
                'icon':'tags'
                },
            'kv':{
                'template':'sidebar/kv',
                'title':'Key/Value',
                'label':'kv',
                'icon':'tasks'
                },
            'media':{
                'template':'sidebar/page_media',
                'title':'Media',
                'label':'media',
                'icon':'picture'
                }
            }
        }
    }


def render_sidebar(**k):

    from core.libs.bottle import template

    panels = panels_dict[k['panel_set']]['panel_order']
    panel_set = panels_dict[k['panel_set']]['panels']
    sidebar_panels = []

    for n in panels:
        panels_n = panel_set[n]
        if not 'collapse' in panels_n:
            panels_n['collapse'] = ''
        panel_body = template(panels_n['template'], **k)
        panel = template('sidebar/panel',
            body=panel_body,
            **panels_n)
        sidebar_panels.append(panel)

    sidebar_template = template('sidebar/sidebar_ui', panels=''.join(sidebar_panels))

    return sidebar_template

def register_sidebar(**k):

    sidebar_to_add = k.get('add_to', None)
    sidebar_panel = k.get('panel', None)

    panels_dict[sidebar_to_add]['panel_order'].append(sidebar_panel['title'])
    panels_dict[sidebar_to_add]['panels'][sidebar_panel['title']] = sidebar_panel
