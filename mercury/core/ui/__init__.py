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


search_contexts = (
    {'blog':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id),
            'form_description':'Search entries:',
            'form_placeholder':'Entry title, term in body text'},
    'blog_media':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/media",
            'form_description':'Search media:',
            'form_placeholder':'Media title, term in description, URL, etc.'},
    'blog_media_pages':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.blog.id) + "/media/" + str(x.id),
            'form_description':'Search pages associated with media:',
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

def listing(request, context_object, item_list_object, colset, menu,
            user=None, rowset_callback=None, errormsg=None, search_ui=None,
            search_context=None, tags_data={}, msg_float=True):

    '''
    Listing framework.
    Used to present a searchable and sortable list of objects.

    request
    The current request object.

    context_object
    An object that provides context for the listing,
    so that it can be used to generate action buttons, etc.
    For instance, for a list of pages in a blog, it's the blog object.
    Example: blog

    item_list_object
    The data object from which we derive the actual listing.
    Example: blog.pages

    search_ui
    The description of the search context to use for the search UI.
    Example: 'blog'

    search_context
    The search context object to use to produce search results
    Example: blog_search_results

    '''

    colset = colsets[colset]

    action_button = colset.get('buttons', None)
    # Any action button to be displayed.

    list_actions = colset.get('list_actions', None)
    # Any list actions to the shown.

    if action_button is not None:
        action_button = ''.join([utils.action_button(n[0], n[1](context_object)) for n in action_button])
    else:
        action_button = None

    if list_actions is not None:
        s = []
        for n in list_actions:
            s.append([n[0], n[1](context_object)])
        list_actions = s

    try:
        items_searched, search = search_context(request, context_object)
    except (UnboundLocalError, KeyError, ValueError, TypeError):
        items_searched, search = None, None

    item_list = item_list_object

    if items_searched is not None:
        item_list = item_list.where(item_list_object.model_class.id << items_searched)

    # basic ordering functionality

    if 'order_by' in request.query:
        item_list = item_list.order_by(
            getattr(item_list_object.model_class, request.query['order_by'], 'title').desc()
            )

    # TODO: pass on the pagination parameters
    # we could do this by keeping a list of the pagination paramters that need to be worked with somewhere
    # need to figure out how to extract, modify, and replace - see url tools

    paginator, rowset = utils.generate_paginator(item_list, request)

    tags = template_tags(search=search, user=user, **tags_data)

    tags.status = errormsg if errormsg is not None else None

    # Use 'rowset_callback' to supply a function that can be used
    # to transform the rowset before display

    if rowset_callback is not None:
        rowset = rowset_callback(rowset)

    if search_ui is not None:
        tags.search_context = (search_contexts[search_ui], context_object)


    # also, if we have template_tags handle search objs,
    # perhaps we should centralize that there instead of
    # adding the search_context here manually!

    # TODO: fix inconsistencies where we parse for nonexistent object vs.
    # object set to None in templates. We should pick a standard behavior

    tpl = _tpl('listing/listing_ui',
        paginator=paginator,
        menu=generate_menu(menu, context_object),
        rowset=rowset,
        colset=colset,
        icons=icons,
        action=action_button,
        list_actions=list_actions,
        msg_float=msg_float,
        **tags.__dict__)

    return tpl
