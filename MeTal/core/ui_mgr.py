panels_dict = {
    'edit_media':
        {'panel_order':['kv', ],
        'panels':
            {
            'kv':{
                'template':'sidebar/sidebar_kv_ui',
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
                'template':'sidebar/sidebar_template_publishing_ui',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'},
            'status':{
                'template':'sidebar/sidebar_template_status_ui',
                'title':'Status',
                'label':'status',
                'icon':'info-sign'
                },
            'theme':{
                'template':'sidebar/sidebar_template_theme_ui',
                'title':'Theme',
                'label':'theme',
                'icon':'file'
                },
            'files':{
                'template':'sidebar/sidebar_template_output_ui',
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
                'template':'sidebar/sidebar_page_publishing_ui',
                'title':'Publishing',
                'label':'publishing',
                'icon':'book',
                'collapse':' in'
                },
            'status':{
                'template':'sidebar/sidebar_page_status_ui',
                'title':'Page status',
                'label':'status',
                'icon':'info-sign'
                },
            'categories':{
                'template':'sidebar/sidebar_page_categories_ui',
                'title':'Categories',
                'label':'categories',
                'icon':'th-list'
                },
            'tags':{
                'template':'sidebar/sidebar_page_tags_ui',
                'title':'Tags',
                'label':'tags',
                'icon':'tags'
                },
            'kv':{
                'template':'sidebar/sidebar_kv_ui',
                'title':'Key/Value',
                'label':'kv',
                'icon':'tasks'
                },
            'media':{
                'template':'sidebar/sidebar_page_media_ui',
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
        panel = template('sidebar/sidebar_panel_ui',
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
