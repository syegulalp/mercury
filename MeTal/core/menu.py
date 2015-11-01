from core import cms
from core.models import get_page, page_status
from core.utils import date_format, html_escape, breaks, utf8_escape
from settings import BASE_URL

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
<li{}><a href="{}">{}</a></li>
'''

label_string = ' <li class="active">{}</li>'

button_string = ' <li><span class="btn-group"><a title="{}" type="button" class="btn btn-default btn-xs" href="{}">{}</a></span></li>'

divider_string = ' role="presentation" class="dropdown-header '

icons = {
    'Unpublished': ('pencil', 'orange', 'Unpublished'),
    'Published': ('ok-sign', 'green', 'Published'),
    'Scheduled': ('time', '#5bc0de', 'Scheduled for publication')
}

menus = {
    'system': {
        'parent': None,
        'path': lambda x: BASE_URL,
        'label': 'Dashboard',
        'menu_title': lambda x: 'Main menu',
        'menu': (
            # 'system_settings',
            'dashboard', 'system_queue', 'system_log', 'system_plugins',
            'system_info',
            'sites_div', 'all_sites', 'create_site'),
    },
    'system_info': {
        'parent': 'system',
        'label': 'System information',
        'path': lambda x: '/system/info',
        'parent_ref': _none,
    },
    'sites_div': {
        'label': 'Sites',
        'divider': True
    },
    'create_site': {
        'parent': 'system',
        'label': 'Create site',
        'path': lambda x: '/system/create-site',
        'parent_ref': _none,
    },
    'dashboard': {
        'parent': None,
        'path': lambda x: '',
        'label': 'Dashboard',
        'paernt_ref': _none},
    'all_sites': {
        'parent': 'system',
        'label': 'Manage sites',
        'path': lambda x: '/system/sites',
        'parent_ref': _none,
    },
    'system_settings': {
        'parent': 'system',
        'label': 'System settings',
        'path': lambda x: '/system/settings',
        'parent_ref': _none,
    },
    'system_log': {
        'parent': 'system',
        'label': 'Activity log',
        'path': lambda x: '/system/log',
        'parent_ref': _none,
    },
    'system_queue': {
        'parent': 'system',
        'label': 'Publishing queue',
        'path': lambda x: "/system/queue",
        'parent_ref': _none,
    },
    'system_plugins': {
        'parent': 'system',
        'label': 'Plugins',
        'path': lambda x: "/system/plugins",
        'parent_ref': _none,
    },
    'site': {
        'parent': 'system',
        'parent_ref': _none,
        'label': 'Manage blogs',
        'menu_title': lambda x: x.name,
        'path': lambda x: BASE_URL + "/site/{}".format(x.id),
        'menu': ('site_users_div', 'site_manage_users', 'site_create_users',
                 'blogs_div', 'manage_blogs', 'create_blog')
    },
    'site_users_div': {
        'label': 'Users',
        'divider': True
    },
    'site_manage_users': {
        'parent': 'site',
        'label': 'Manage users',
        'path': lambda x: "/users",
        'parent_ref': _self,
    },
    'site_manage_user': {
        'parent': 'site',
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'path': lambda x: BASE_URL + "/site/{}/users".format(x.site.id),
        'button': lambda x: 'Users',
        'button_title': 'All users on this site',
        'parent_ref': lambda x: x.site,
    },
    'site_create_users': {
        'parent': 'site',
        'label': 'Create users',
        'path': lambda x: "/create-user",
        'parent_ref': _self,
    },
    'blogs_div': {
        'label': 'Blogs',
        'divider': True
    },
    'manage_blogs': {
        'parent': 'site',
        'label': 'Manage blogs',
        'path': lambda x: "/blogs",
        'parent_ref': _self,
    },
    'create_blog': {
        'parent': 'site',
        'label': 'Create blog',
        'path': lambda x: "/create-blog",
        'parent_ref': _self,
    },

    'blog': {
        'parent': 'site',
        'parent_ref': lambda x: x.site,
        'label': 'Manage pages',
        'path': lambda x: BASE_URL + '/blog/{}'.format(x.id),
        'menu_title': lambda x: x.name,
        'menu': ('pages_div', 'manage_pages', 'create_page', 'categorization_div', 'blog_manage_categories',
                'blog_manage_tags', 'media_div',
                'blog_manage_media', 'design_div', 'blog_manage_templates', 'blog_settings'),
    },
    'blog_settings': {
        'parent': 'blog',
        'label': 'Blog settings',
        'path': lambda x: "/settings",
        'button_title': 'Settings',
        'parent_ref': lambda x: x,
    },
    'categorization_div': {
        'label': 'Categorization',
        'divider': True
    },
    'design_div': {
        'label': 'Design',
        'divider': True
    },
    'blog_manage_categories': {
        'parent': 'blog',
        'label': 'Categories',
        'path': lambda x: "/categories",
        'parent_ref': _self,
    },
    'blog_manage_tags': {
        'parent': 'blog',
        'label': 'Tags',
        'path': lambda x: "/tags",
        'parent_ref': _self,
    },
    'blog_manage_templates': {
        'parent': 'blog',
        'label': 'Templates',
        'path': lambda x: "/templates",
        'parent_ref': _self,
    },
    'blog_template': {
        'parent': 'blog',
        'path': lambda x: BASE_URL + "/blog/{}/templates".format(x.blog.id),
        'button': lambda x: 'Templates',
        'button_title': 'All templates in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_edit_template': {
        'parent': 'blog',
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'path': lambda x: BASE_URL + "/blog/{}/templates".format(x.blog.id),
        'button': lambda x: 'Templates',
        'button_title': 'All templates in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_delete_template': {
        'parent': 'blog_template',
        'button_label': lambda x: 'Delete',
        'path': lambda x: BASE_URL + "/template/{}/edit".format(x.id),
        'button': lambda x: 'Edit #{}'.format(x.id),
        'button_title': '',
        'parent_ref': lambda x: x,
    },
    'media_div': {
        'label': 'Media',
        'divider': True
    },
    'blog_queue': {
        'parent': 'blog',
        'label': 'Blog publishing queue',
        'path': lambda x: "/blog/{}".format(x.id),
        'parent_ref': lambda x: x
    },
    'blog_purge': {
        'parent': 'blog',
        'label': 'Purge and recreate blog',
        'path': lambda x: "/blog/{}".format(x.id),
        'parent_ref': lambda x: x
    },
    'blog_republish': {
        'parent': 'blog',
        'label': 'Republish blog',
        'path': lambda x: "/blog/{}".format(x.id),
        'parent_ref': lambda x: x
    },
    'blog_manage_media': {
        'parent': 'blog',
        'label': 'Manage media',
        'path': lambda x: "/media",
        'parent_ref': _self,
    },
    'edit_page': {
        'parent': 'blog',
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'path': lambda x: BASE_URL + "/blog/{}".format(x.blog.id),
        'button': lambda x: 'Pages',
        'button_title': 'All pages in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'edit_tag': {
        'parent': 'blog_manage_tags',
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'path': lambda x: BASE_URL + "/blog/{}/tags".format(x.blog.id),
        'button': lambda x: 'Tags',
        'button_title': 'All tags in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'edit_category': {
        'parent': 'blog',
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'path': lambda x: BASE_URL + "/blog/{}/categories".format(x.blog.id),
        'button': lambda x: 'Categories',
        'button_title': 'All categories in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_media': {
        'parent': 'blog',
        'path': lambda x: BASE_URL + "/blog/{}/media".format(x.blog.id),
        'button': lambda x: 'Media',
        'button_title': 'All media in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_edit_media': {
        'parent': 'blog',
        'path': lambda x: BASE_URL + "/blog/{}/media".format(x.blog.id),
        'button_label': lambda x: 'Edit #{}'.format(x.id),
        'button': lambda x: 'Media',
        'button_title': 'All media in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_delete_media': {
        'parent': 'blog_media',
        'button_label': lambda x: 'Delete',
        'path': lambda x: BASE_URL + "/blog/{}/media/{}/edit".format(x.blog.id, x.media.id),
        'button': lambda x: 'Edit #{}'.format(x.media.id),
        'button_title': 'Return to editing media',
        'parent_ref': lambda x: x.media,
    },

    'pages_div': {
        'label': 'Pages',
        'divider': True
    },
    'manage_pages': {
        'parent': 'blog',
        'label': 'Manage pages',
        'path': lambda x: "",
        'parent_ref': _self,
    },
    'create_page': {
        'parent': 'blog',
        'label': 'Create page',
        'path': lambda x: "/newpage",
        'parent_ref': _self,
    },
    'new_category': {
        'parent': 'blog',
        'button_label': lambda x: 'Create new category',
        'path': lambda x: BASE_URL + "/blog/{}/categories".format(x.blog.id),
        'button': lambda x: 'Categories',
        'button_title': 'All categories in this blog',
        'parent_ref': lambda x: x.blog,
    },
    'blog_categories': {
        'parent': 'blog',
        'path': lambda x: BASE_URL + "/blog/{}/categories".format(x.id),
        'button': lambda x: 'Categories',
        'button_title': 'All categories in this blog',
        'parent_ref': lambda x: x,
    },
    'delete_category': {
        'parent': 'blog_categories',
        'button_label': lambda x: 'Delete',
        'path': lambda x: BASE_URL + "/blog/{}/category/{}".format(x.blog.id, x.id),
        'button': lambda x: 'Edit #{}'.format(x.id),
        'button_title': 'Return to editing category',
        'parent_ref': lambda x: x.blog,
    },
}


def generate_menu(context, context_object):

    menu = ""

    segment = menus[context]

    if 'label' in segment:
        menu = label_string.format(segment['label']) + menu

    while True:

        submenu = []

        parent_path = segment['path'](context_object)

        if 'button' in segment:

            if 'button_label' in segment:
                menu = label_string.format(segment['button_label'](context_object)) + menu

            menu = button_string.format(
                segment['button_title'],
                segment['path'](context_object),
                segment['button'](context_object)) + menu

        if 'menu' in segment:

            for l in segment['menu']:
                g = menus[l]

                path = parent_path + \
                    g['path'](context_object) if 'path' in g else '#'
                divider = divider_string if 'divider' in g else ''

                submenu.append(submenu_string.format(
                    divider, path,
                    g['label']))

            menu = segment_string.format(
                segment['menu_title'](context_object),
                parent_path,
                segment['menu_title'](context_object),
                ''.join(submenu)
            ) + menu

        if segment['parent'] is None:
            break

        new_context = segment['parent_ref'](context_object)
        context_object = new_context
        segment = menus[segment['parent']]

    return menu


colsets = {
    'tags': {
        'none': 'No tags found',
        'colset': [
            {'field': 'tag',
             'label': 'Tag',
             'format_raw': lambda x: x.for_listing
             },
            {'field': 'in_pages',
             'label': 'Pages',
             'format_raw': lambda x: x.in_pages.count()
             }
        ]
    },
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
        )
    },
    'blog': {
        'none': 'No pages found',
        'xrowclass': 'overflow',
        'actions': (
            {'unpublish': {
                'label': 'Unpublish',
                'action': lambda x: cms.unpublish_page(get_page(x), remove_fileinfo=True)}
             },
            {'republish': {
                'label': 'Republish',
                'action': lambda x: cms.publish_page(get_page(x))}
             },
            {'delete': {
                'label': 'Delete',
                'action': lambda x: cms.delete_page(get_page(x))}
             },
            {'add_tags': {
                'label': 'Add tags',
                'action': lambda x, tag_ids: cms.page_add_tags(get_page(x), tag_ids)}
             },
            {'remove_tags': {
                'label': 'Remove tags',
                'action': lambda x, tag_ids: cms.page_remove_tags(get_page(x), tag_ids)}
             }
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
             'colclass': 'overflow',
             'format': lambda x: x.primary_category.title
             },
            {'field': 'publication_date',
             'label': 'Publish date',
             'colwidth': '1%',
             'xlabel_style': 'width:1%',
             'colclass': 'overflow',
             'format': lambda x: date_format(x.publication_date)
             },
        )
    }

}


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
