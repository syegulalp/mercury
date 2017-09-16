from core.cms import cms
from core.models import Page, page_status
from core.utils import date_format, html_escape, breaks, utf8_escape
from core.cms.queue import job_type
from settings import BASE_URL, PLUGIN_FILE_PATH
from os.path import join as _join

_self = lambda x: x
_id = lambda x: x.id
_none = lambda *args: 0  # @UnusedVariable

segment_string = """
<li title='{}'><span class='btn-group'><a type='button' class='btn btn-default btn-xs' href='{}'>{}</a>
<button class="btn btn-default btn-xs dropdown-toggle" type="button" data-toggle="dropdown" aria-expanded="false">
<span class="caret"></span></button>
<ul class="dropdown-menu" role="menu">
{}
</ul></span></li>"""

submenu_string = '''
<li><a title="{}" href="{}">{}</a></li>
'''

divider_string = '''
<li role="presentation" class="dropdown-header">{}</li>
'''

label_string = ' <li class="active">{}</li>'

button_string = ' <li><span class="btn-group"><a title="{}" type="button" class="btn btn-default btn-xs" href="{}">{}</a></span></li>'

icons = {
    'Unpublished': ('pencil', 'orange', 'Unpublished'),
    'Published': ('ok-sign', 'green', 'Published'),
    'Scheduled': ('time', '#5bc0de', 'Scheduled for publication')
}

menus = {
    'system_menu': {
        'type':'menu',
        'text': lambda x: 'Main menu',
        'parent': None,
        'path': lambda x: BASE_URL,  # Path we go to when we click the main button.
        'menu': (
            'system_div',
            'dashboard_label', 'system_queue', 'system_log', 'system_plugins',
            'system_info',
            'themes_div', 'system_manage_themes',
            'sites_div', 'manage_sites', 'create_site',
            'users_div', 'system_manage_users', 'system_create_user')
    },
    'system_div': {
        'type': 'divider',
        'text': lambda x: 'System',
        },
    'themes_div': {
        'type': 'divider',
        'text': lambda x: 'Theming',
        },
    'dashboard_label':{
        'type':'label',
        'text':lambda x:'Dashboard',
        'hover':'Overview of your posts and other activity',
        'path': lambda x: BASE_URL
    },
    'system_queue': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/queue',
        'text': lambda x: 'System publishing queue',
        'hover':'Systemwide view of all posts queued for publishing',
        'parent':'system_menu'},
    'system_log': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/log',
        'text': lambda x: 'System activity log',
        'hover':'Details about publishing activity, user behaviors, etc.',
        'parent':'system_menu'},
    'system_plugins': {
        'type': 'button',
        'path': lambda x: BASE_URL + '/system/plugins',
        'text': lambda x: 'Plugins',
        'parent':'system_menu'
        },
    'system_plugin_data': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/plugin/{}'.format(x.id),
        'text': lambda x: 'Plugin #{}'.format(x.id),
        'parent':'system_plugins'
        },
    'system_manage_themes': {
        'type': 'button',
        'path': lambda x: BASE_URL + '/system/themes',
        'text': lambda x: 'Themes',
        'parent':'system_menu'
        },
    'system_theme_data': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/theme/{}'.format(x.id),
        'text': lambda x: 'Theme #{}'.format(x.id),
        'parent':'system_manage_themes'
        },
    'system_delete_theme': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/theme/{}/delete'.format(x.id),
        'text': lambda x: 'Delete theme',
        'parent':'system_manage_themes'
        },
    'system_info': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/info',
        'text': lambda x: 'System information',
        'hover':'Information about this application',
        'parent':'system_menu'},
    'sites_div': {
        'type': 'divider',
        'text': lambda x: 'Sites',
        },
    'manage_sites': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/sites',
        'text': lambda x: 'Manage sites',
        'hover':'List all available sites and make changes to them',
        'parent':'system_menu'},
    'create_site': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/site/new',
        'text': lambda x: 'Create site',
        'hover':'Create a new, empty site in this installation',
        'parent':'system_menu'},
    'users_div': {
        'type': 'divider',
        'text': lambda x: 'Users',
        },
    'system_manage_users': {
        'type': 'button',
        'path': lambda x: BASE_URL + '/system/users',
        'text': lambda x: 'Manage users',
        'hover':'List all users for this application',
        'parent':'system_menu'},
    'system_edit_user': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/user/{}'.format(x),
        'text': lambda x: 'Edit user #{}'.format(x.id),
        'parent_context':lambda x:None,
        'hover':'Edit a specific user\'s data',
        'parent':'system_manage_users'},
    'system_create_user': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/system/user/new',
        'text': lambda x: 'Create user',
        'hover':'Create a new user and assign site or blog permissions',
        'parent':'system_menu'
        },
    'site_menu': {
        'type':'menu',
        'text': lambda x: '{}'.format(x.name),
        'path': lambda x: BASE_URL + '/system/sites/',
        'parent': 'system_menu',
        'parent_path': lambda x: x.site,
        'parent_context': lambda x:None,
        'menu': (
            # 'site_users_div', 'site_manage_users', 'site_create_user',
             'blogs_div', 'site_manage_blogs', 'site_create_blog')
        },
    'site_users_div': {
        'type': 'divider',
        'text': lambda x: 'Users',
        },
    'site_manage_users': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/site/{}/users'.format(x.id),
        'text': lambda x: 'Manage users',
        'parent':'site_menu'
        },
    'site_create_user': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/site/{}/user/new'.format(x.id),
        'text': lambda x: 'Create user',
        'parent':'site_menu'
        },
    'blogs_div': {
        'type': 'divider',
        'text': lambda x: 'Blogs',
        },
    'site_manage_blogs': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/site/{}'.format(x.id),
        'text': lambda x: 'Manage blogs',
        'parent_context': lambda x: x,
        'parent':'site_menu'
        },
    'site_create_blog': {
        'type': 'label',
        'path': lambda x: BASE_URL + '/site/{}/blog/new'.format(x.id),
        'text': lambda x: 'Create blog',
        'parent_context': lambda x: x,
        'parent':'site_menu',
        },
    'blog_menu': {
        'type':'menu',
        'text': lambda x: '{}'.format(x.name),
        'path': lambda x: BASE_URL + '/blog/{}'.format(x.id),
        'parent': 'site_menu',
        'parent_context': lambda x: x.site,
        'menu': ('pages_div', 'manage_pages', 'create_page', 'categorization_div',
            'blog_manage_categories',
                'blog_manage_tags', 'media_div',
                'blog_manage_media', 'design_div', 'blog_manage_templates',
                'blog_manage_themes', 'blog_settings',
                 # 'blog_users_div', 'blog_manage_users', 'blog_create_user'
                 )
                 },
    'pages_div': {
        'type': 'divider',
        'text': lambda x:'Pages',
        },
    'manage_pages': {
        'type': 'button',
        'text': lambda x:'Manage pages',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}'.format(x.id),
        },
    'edit_page':{
        'type':'label',
        'text': lambda x:'Edit page #{}'.format(x.id),
        'parent':'manage_pages',
        'parent_context':lambda x:x.blog
    },
        # 'path': lambda x: BASE_URL + '/blog/{}/newpage'.format(x.id),
    'create_page':{
        'type':'label',
        'text': lambda x:'Create page',
        'parent':'blog_menu',
        'path': lambda x: BASE_URL + '/blog/{}/newpage'.format(x.id),
        'parent_context':lambda x:x
        },
    'categorization_div':{
        'type':'divider',
        'text':lambda x:'Categorization'},
    'blog_manage_categories':{
        'type':'button',
        'parent':'blog_menu',
        'path': lambda x: BASE_URL + '/blog/{}/categories'.format(x.id),
        'text':lambda x:'Categories',
        'parent_context':lambda x:x
        },
    'blog_edit_category':{
        'type':'label',
        'parent':'blog_manage_categories',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/category/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Edit category #{}'.format(x.id)
        },
    'blog_edit_category_button':{
        'type':'button',
        'parent':'blog_manage_categories',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/category/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Category #{}'.format(x.id)
        },
    'blog_delete_category':{
        'type':'label',
        'parent':'blog_edit_category_button',
        'parent_context':lambda x:x,
        # 'path': lambda x: BASE_URL + '/blog/{}/category/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Delete category #{}'.format(x.id)
        },
    'blog_pages_in_category':{
        'type':'label',
        'parent':'blog_edit_category_button',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/category/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Pages in {}'.format(x.for_log)
        },
    'blog_new_category':{
        'type':'label',
        'parent':'blog_manage_categories',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/newcategory'.format(x.blog.id, x.id),
        'text':lambda x:'Add new category'
        },
    'blog_manage_tags':{
        'type':'button',
        'parent':'blog_menu',
        'path': lambda x: BASE_URL + '/blog/{}/tags'.format(x.id),
        'parent_context':lambda x:x,
        'text':lambda x:'Tags'},
    'blog_edit_tag':{
        'type':'label',
        'parent':'blog_manage_tags',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/tag/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Edit tag #{}'.format(x.id)
        },
    'blog_edit_tag_button':{
        'type':'button',
        'parent':'blog_manage_tags',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/tag/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Tag #{}'.format(x.id)
        },
    'blog_delete_tag':{
        'type':'label',
        'parent':'blog_edit_tag_button',
        'parent_context':lambda x:x,
        # 'path': lambda x: BASE_URL + '/blog/{}/tag/{}'.format(x.blog.id, x.id),
        'text':lambda x:'Delete tag #{}'.format(x.id)
        },
    'blog_pages_for_tag':{
        'type':'label',
        'parent':'blog_edit_tag_button',
        'parent_context':lambda x:x,
        # 'path': lambda x: BASE_URL + '/blog/{}/tag/{}'.format(x.blog.id, x.id),
        # 'text': lambda x:'Edit tag #{}'.format(x.id)},
        'text': lambda x:'Pages with {}'.format(x.for_log),
        },
    'blog_edit_media_button':{
        'type':'button',
        'parent':'blog_manage_media',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/media/{}/edit'.format(x.blog.id, x.id),
        'text':lambda x:'Edit media #{}'.format(x.id)},
    'blog_media_pages':{
        'type':'label',
        'parent':'blog_edit_media_button',
        'parent_context':lambda x:x,
        # 'path': lambda x: BASE_URL + '/blog/{}/tag/{}'.format(x.blog.id, x.id),
        # 'text': lambda x:'Edit tag #{}'.format(x.id)},
        'text': lambda x:'Pages with media #{}'.format(x.id),
        },
    'media_div':{
        'type':'divider',
        'text':lambda x:'Media'},
    'blog_manage_media':{
        'type':'button',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/media'.format(x.id),
        'text':lambda x:'Manage media'},
    'blog_edit_media':{
        'type':'label',
        'parent':'blog_manage_media',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/media'.format(x.id),
        'text':lambda x:'Edit media #{}'.format(x.id)},
    'blog_delete_media':{
        'type':'label',
        'parent':'blog_manage_media',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/blog/{}/media'.format(x.blog.id),
        'text':lambda x:'Delete media #{}'.format(x.id)},
    'design_div':{
        'type':'divider',
        'parent':'blog_menu',
        'text':lambda x:'Design'},
    'blog_manage_templates':{
        'type':'button',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/templates'.format(x.id),
        'text':lambda x:'Templates'},
    'blog_edit_template':{
        'type':'label',
        'parent':'blog_manage_templates',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/template/{}/edit'.format(x.id),
        'text':lambda x:'Edit template #{}'.format(x.id)},
    'blog_delete_template':{
        'type':'label',
        'parent':'blog_manage_templates',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/template/{}/delete'.format(x.id),
        'text':lambda x:'Delete template #{}'.format(x.id)},
    'blog_delete_page':{
        'type':'label',
        'parent':'manage_pages',
        'parent_context':lambda x:x.blog,
        'path': lambda x: BASE_URL + '/page/{}/delete'.format(x.id),
        'text':lambda x:'Delete page #{}'.format(x.id)},
    'blog_manage_themes':{
        'type':'button',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/themes'.format(x.id),
        'text':lambda x:'Themes'
        },
    'blog_settings':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/settings'.format(x.id),
        'text':lambda x:'Blog settings'
        },
    'blog_import':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/import'.format(x.id),
        'text':lambda x:'Import data to blog'
        },
    'blog_users_div':{
        'type':'divider',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'text':lambda x:'Users'},
    'blog_manage_users':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/users'.format(x.id),
        'text':lambda x:'Manage users'
        },
    'blog_republish':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/republish'.format(x.id),
        'text':lambda x:'Republish blog'
        },
    'blog_purge':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/purge'.format(x.id),
        'text':lambda x:'Purge blog'
        },
    'blog_queue':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/publish'.format(x.id),
        'text':lambda x:'Blog publishing queue'
        },
    'blog_create_user':{
        'type':'label',
        'parent':'blog_menu',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/user/new'.format(x.id),
        'text':lambda x:'Create user'
        },
    'blog_apply_theme':{
        'type':'label',
        'parent':'blog_manage_themes',
        'parent_context':lambda x:x[0],
        'path': lambda x: BASE_URL + '/blog/{}/theme/{}/apply'.format(x[0].id),
        'text':lambda x:'Apply theme'
        },
    'blog_save_theme':{
        'type':'label',
        'parent':'blog_manage_themes',
        'parent_context':lambda x:x,
        'path': lambda x: BASE_URL + '/blog/{}/theme/save'.format(x.id),
        'text':lambda x:'Save this blog\'s theme'
        },
}

colsets = {
    'plugins': {
        'none':'No plugins found',
        'colset':[
            {'field':'name',
                'label':'Name',
                'format_raw':lambda x:(
                    x.for_display if x.enabled is True
                    else '<i>{}</i>'.format(
                    _join(PLUGIN_FILE_PATH, x.path)
                    )
                    )
            },
            {'field':'description',
                'label':'Description',
                'format_raw':lambda x:x.description
            },
            {'field':'path',
                'label':'Path to plugin',
                'format':lambda x:'{}'.format(
                    _join(PLUGIN_FILE_PATH, x.path)
                    )
            },
            {'field':'status',
                'label':'Status',
                'format_raw':lambda x: (
                    '<a href="{}/system/plugin/{}/disable"><span class="label label-success">Enabled</span></a>'.format(
                        BASE_URL, x.id) if x.enabled
                        else '<a href="{}/system/plugin/{}/enable"><span class="label label-default">Disabled</span></a>'.format(
                        BASE_URL, x.id)
                        )
                }
            ]
        },
    'system_users': {
        'none': 'No users found',
        'colset': [
            {'field': 'name',
             'label': 'Name',
             'format_raw': lambda x: x.for_listing
             },
        ]
    },
    'themes': {
        'none': 'No themes found',
        'colset': [
            {'field': 'title',
             'label': 'Title',
             'format_raw': lambda x:x.for_listing
                # lambda x: '{}<br/><small>{}</small>'.format(
                # x.for_listing,
                # x.description)
             },
            {'field': 'description',
             'label': 'Description',
             'format': lambda x: x.description
             },
            {'field': '',
             'label': '',
             'format_raw':lambda x:('<a href="{}"><span class="label label-primary">Current blog theme</span></a>{}'.format(
                 '{}/system/theme/{}'.format(BASE_URL, x.id), ' <a href="{}"><span class="label label-danger">Modified by blog</span></a>'.format(
                     '{}/blog/{}/templates').format(BASE_URL, x.blog.id)
                     if x.blog.theme_modified is True else '') if x.blog.theme.id == x.id else '')
             },
             {'field': 'default',
             'label': '',
             'format_raw': lambda x: '<span class="label label-warning">Default theme for new blogs</span>' if x.is_default else ''
             },
            {'field': '',
             'label': '',
             'format_raw':lambda x:'<a href="{}"><span class="label label-success pull-right">Apply theme</span></a>'.format(
                 '{}/blog/{}/theme/{}/apply'.format(BASE_URL, x.blog.id, x.id),)
             }
        ]
    },
    'themes_site': {
        'none': 'No themes found',
        'colset': [
            {'field': 'title',
             'label': 'Title',
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'description',
             'label': 'Description',
             'format': lambda x: x.description
             },
             {'field': 'default',
             'label': '',
             'format_raw': lambda x: '<span class="label label-warning">Default theme for new blogs</span>' if x.is_default else ''
             },
             {'field': '',
             'label': '',
             'format_raw':lambda x:'<a href="{}"><span class="label label-danger pull-right">Delete theme</span></a>'.format(
                 '{}/system/theme/{}/delete'.format(BASE_URL, x.id),)
             }
        ]
    },
    'tags': {
        'none': 'No tags found',
        'colset': [
            {'field': 'tag',
             'label': 'Tag',
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'in_pages',
             'label': 'Pages',
             'format_raw': lambda x: "<a href='{}/blog/{}/tag/{}/pages'>{}</a>".format(
                 BASE_URL,
                 x.blog.id,
                 x.id,
                 x.pages.count()
                 )
             }
        ]
    },
    'queue':{
        'none':'No items pending in queue',
        'buttons':(
            ('Clear queue', lambda n:'queue/clear'),
            # we do this because the queue could be blog, site, or sitewide
            ),
        'colset':[
            {'field':'priority',
             'label':'Priority',
             'colwidth': '1%',
             'format':lambda x:x.priority
             },
            {'field':'job_type',
             'label':'Job type',
             'colwidth': '10%',
             'colclass': 'overflow',
             'format':lambda x: job_type.description[x.job_type]
             },
            {'field':'data_string',
             'label':'Description',
             'colclass': 'overflow',
             'format_raw':lambda x: x.data_string
             },
            {'field':'date',
             'label':'Date inserted',
             'format_raw':lambda x: date_format(x.date_touched)
             }
            ]},
    'categories': {
        'none': 'No categories found',
        'colset': [
            {'field': 'title',
             'label': 'Category',
             'format_raw': lambda x: x.for_listing
             },
             {'field': 'child_of',
             'label': 'Parent',
             'format_raw': lambda x: x.parent_c.for_listing
             },
             {'field': 'pages',
             'label': 'Pages in category',
             'format_raw': lambda x: "<a href='{}/blog/{}/category/{}/pages'>{}</a>".format(
                 BASE_URL,
                 x.blog.id,
                 x.id,
                 x.pages.count()
                 )
             },
             {'field':'default',
             'label':'Default',
             'format_raw':lambda x:'<span class="label label-warning">Default blog category</span>' if x.default is True else ''
             }
        ]
    },
    'system_log': {
        'none': 'No log entries found',
        'colset': [
            {'field': 'date',
             'label': 'Timestamp',
             'xlabel_style': 'width:1%',
             'colclass': 'overflow',
             'colwidth': '1%',
             'format': lambda x: date_format(x.date)
             },
            {'field': 'message',
             'label': 'Log entry',
             'colclass': 'xoverflow',
             'colwidth': '*',
             'format': lambda x: x.message

             }
        ]
    },
    'all_sites': {
        'none': 'No pages found',
        'actions': (),
        'colset': (
            {'field': 'name',
             'label_style': 'width:25%',
             'label': 'Name',
             # 'raw':True,
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'description',
             'label_style': 'width:75%',
             'label': 'Description',
             'format': lambda x: x.description
             },
        )
    },
    'site': {
        'none': 'No pages found',
        'actions': (),
        'colset': (
            {'field': 'name',
             'label_style': 'width:25%',
             'label': 'Name',
             # 'raw':True,
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'description',
             'label_style': 'width:75%',
             'label': 'Description',
             'format': lambda x: x.description
             },
        )},
    'media': {
        'none': 'No media found',
        'actions': (),
        'colset': (
            {'field': 'friendly_name',
             'colwidth': '*',
             'label': 'Name',
             'format_raw': lambda x: x.for_listing},
            {'field': 'preview',
             'colwidth': '1%',
             'label': 'Preview',
             'format_raw': lambda x: x.preview_for_listing},
            {'field': 'filename',
             'label': 'Filename',
             'colwidth': '1%',
             'format': lambda x: x.filename},
            {'field': 'path',
             'label': 'Path',
             'colwidth': '20%',
             'format_raw': lambda x: breaks(utf8_escape(x.path))},
             {'field': 'url',
             'label': 'URL',
             'colwidth': '20%',
             'format_raw': lambda x: '<a target="_blank" href="{}">{}</a>'.format(x.url, breaks(utf8_escape(x.url)))
             },
             {'field': 'pages',
             'label': 'Used in',
             'colwidth': '1%',
             'format_raw': lambda x: '<a target="_blank" href="{}">{}</a>'.format(
                 "/blog/{}/media/{}/pages".format(x.blog.id, x.id),
                 x.pages.count()
                 )
             },

        )
    },
    'blog_users':{
        'none':'No users found',
        'colset':({
            'field':'user_name',
            'label': 'User',
            'format_raw': lambda x:x.for_display
            },)
    },
    'blog': {
        'none': 'No pages found',
        'xrowclass': 'overflow',
        'buttons':(
            ('Create new page', lambda blog:'{}/blog/{}/newpage'.format(BASE_URL, blog.id)),
            ),
        'list_actions':(
            ('Republish', lambda blog:'{}/blog/{}/republish-batch'.format(BASE_URL, blog.id)),
            ),
        'colset': (
            {'field': 'status',
             'xlabel_style': 'width:1%',
             'label': 'Status',
             'colwidths': ('1%', '1%'),
             'label_colspan': '2',
             # 'raw':True,
             'format_raw': lambda x: _page_status_icons(x)
             },
            {'field': 'title',
             'label': 'Title',
             'colwidth': '',
             'xlabel_style': 'width:*',
             'colclass': 'overflow max-width',
             # 'raw':True,
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'user',
             'label': 'Author',
             'colwidth': '1%',
             'colclass': 'overflow',
             'xlabel_style': 'width:1%',
             # 'raw':True,
             'format_raw': lambda x: x.user.from_blog(x.blog).for_display
             },
            {'field': 'primary_category',
             'label': 'Category',
             'colwidth': '1%',
             'xlabel_style': 'width:1%',
             'colclass': 'overflow max-width',
             'format_raw': lambda x: x.primary_category.for_listing
             },
            {'field': 'publication_date_tz',
             'label': 'Publish date',
             'colwidth': '1%',
             'xlabel_style': 'width:1%',
             'colclass': 'overflow',
             'format': lambda x: date_format(x.publication_date_tz)
             },
        )
    }

}


def generate_menu(context, context_object):
    menu = []
    segment = menus[context]

    while True:
        stype = segment['type']
        if stype == 'menu':
            _ = []
            for l in segment['menu']:
                g = menus[l]

                if g['type'] == 'divider':
                    sstr = divider_string.format(g['text'](context_object))
                elif g['type'] == 'button':
                    sstr = submenu_string.format(
                        g.get('hover', ''),
                        g['path'](context_object),
                        g['text'](context_object))
                elif g['type'] == 'label':
                    sstr = submenu_string.format(
                        g.get('hover', ''),
                        g['path'](context_object),
                        g['text'](context_object))

                _.append(sstr)

            m2 = segment_string.format(
                segment['text'](context_object),
                segment['path'](context_object),
                segment['text'](context_object),
                ''.join(_))

            menu.insert(0, m2)

        elif stype == 'label':
            menu.insert(0, label_string.format(segment['text'](context_object)))
        elif stype == 'button':
            menu.insert(0, button_string.format(

                segment['text'](context_object),
                segment['path'](context_object),
                segment['text'](context_object),

                ))

        if segment['parent'] is None:
            break

        try:
            new_context = segment['parent_context'](context_object)
        except:
            new_context = None
        context_object = new_context
        segment = menus[segment['parent']]

    return ''.join(menu)


def _add_colset(item, obj, predecessor):
    pass


def _add_action(item, obj, predecessor):
    n = colsets[obj]['actions']
    new_colset = ()
    for q in n:
        for i in q.keys():
            if i == predecessor:
                new_colset += item
            else:
                new_colset += (q,)

    colsets[obj]['actions'] = new_colset


def _remove_colset(item):
    pass


def _remove_action(item):
    pass


def _page_listing(page):

    if page.title:
        page_title = html_escape(page.title)
    else:
        page_title = "[<i>Untitled</i>]"

    return '<a href="{}/page/{}/edit">{}</a>'.format(
        BASE_URL,
        page.id,
        page_title
    )


def _page_status_icons(page):

    icon = icons[page.status]

    page_status_icon = '''
<span title="{}" style="color:{}"
class="glyphicon glyphicon-{}" aria-hidden="true"></span>'''.format(
        icon[2],
        icon[1],
        icon[0])

    page_permalink_icon = ''

    if page.status == page_status.published:
        page_permalink_icon = '''
<a target="_blank" title="See published page" href="{}">
<span class="glyphicon glyphicon-share"></span></a>'''.format(page.permalink)

    return page_status_icon + "</td><td>" + page_permalink_icon
