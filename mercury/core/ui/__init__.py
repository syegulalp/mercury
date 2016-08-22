from core.models import template_tags
from core import utils
from core.libs.bottle import template as _tpl
from core.menu import generate_menu, colsets, icons
from settings import BASE_URL

queue_selections = (
    ('Remove from queue', '1', ''),
    ('Change queue priority', '2', '')
    )

status_badge = ('', 'warning', 'success', 'info')

save_action = (
    (None),
    (1, 'Save draft'),
    (3, 'Save & update live'),
    (1, 'Save draft')
    )


search_context = (
    {'blog':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id),
            'form_description':'Search entries:',
            'form_placeholder':'Entry title, term in body text'},
    'blog_media':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/media",
            'form_description':'Search media:',
            'form_placeholder':'Media title, term in description, URL, etc.'},
    'blog_templates':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/templates",
            'form_description':'Search templates:',
            'form_placeholder':'Template title or text in template'},
    'blog_tags':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/tags",
            'form_description':'Search tags:',
            'form_placeholder':'Tag name'},
    'blog_pages_with_tag':
            {'form_target': lambda x: "{}/blog/{}/tag/{}/pages".format(
                BASE_URL, x.blog.id, x.id),
                # lambda x: BASE_URL + "/blog/" + str(x.id) + "/tags",
            'form_description':'Search pages with this tag:',
            'form_placeholder':'Page title or text in description'},
    'blog_pages_in_category':
            {'form_target': lambda x: "{}/blog/{}/category/{}/pages".format(
                BASE_URL, x.blog.id, x.id),
                # lambda x: BASE_URL + "/blog/" + str(x.id) + "/tags",
            'form_description':'Search pages in this category:',
            'form_placeholder':'Page title or text in description'},
    'site':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search blogs:',
            'form_placeholder':'Page title or text in description'},
    'sites':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search sites:',
            'form_placeholder':'Site title or text in description'},
    'blog_queue':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/queue",
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
    'site_queue':
            {'form_target':lambda x: BASE_URL + "/site/queue",  # @UnusedVariable
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
     'system_log':
            {'form_target':lambda x: BASE_URL + "/system/log",  # @UnusedVariable
            'form_description':'Search log:',
            'form_placeholder':'Log entry data, etc.'}
    }
    )

def listing(request, user, errormsg, context, tags_data,
    colset_source=colsets, search_context_source=search_context):
    '''
    Listing framework.
    Used to present a searchable and sortable list of objects.
    '''
    # tags_data = {'blog_id':blog.id}
    # This is any data to pass to the template_tags function.

    # context:
    search_context_obj = context['search_context']
    # The search context object to use to produce search results.
    # Example: blog_search_results
    search_ui = context['search_ui']
    # The description of the search context to use for the search UI.
    # 'blog'
    colset = context['colset']
    # The column set to use for the listing.
    # 'blog'
    menu = context['menu']
    # The menu set to use for the listing page.
    # 'blog_menu'
    search_object = context['search_object']
    # The object to be passed to the search context.
    # blog
    item_list_object = context['item_list_object']
    # For future use when we perform search ordering.
    # blog.pages
    action_button = context.get('action_button', None)
    # Any action button to be displayed.
    # (action button)
    list_actions = context.get('list_actions', None)
    # Any list actions to the shown.
    # (list actions)

    if action_button is not None:
        action_button = utils.action_button(*action_button)
    else:
        action_button = ''

    try:
        items_searched, search = search_context_obj(request, search_object)
    except (KeyError, ValueError, TypeError):
        items_searched, search = None, None

    item_list = item_list_object.select()

    if items_searched is not None:
        item_list = item_list.where(item_list_object.model_class.id << items_searched)

    # basic ordering functionality

    if 'order_by' in request.query:
        item_list = item_list.order_by(
            getattr(item_list_object.model_class, request.query['order_by']).desc()
            )

    # TODO: pass on the pagination parameters

    paginator, rowset = utils.generate_paginator(item_list, request)

    tags = template_tags(
        search=search,
        user=user,
        **tags_data
        )

    tags.status = errormsg if errormsg is not None else None

    # Use 'rowset_callback' to supply a function that can be used
    # to transform the rowset before display

    callback = context.get('rowset_callback', None)
    if callback is not None:
        rowset = callback(rowset)

    tpl = _tpl('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context_source[search_ui], search_object),
        menu=generate_menu(menu, search_object),
        rowset=rowset,
        colset=colset_source[colset],
        icons=icons,
        action=action_button,
        list_actions=list_actions,
        **tags.__dict__)

    return tpl
