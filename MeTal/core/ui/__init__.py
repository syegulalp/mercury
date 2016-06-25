from core.models import template_tags
from core import utils
from core.libs.bottle import template
from core.menu import generate_menu, colsets, icons
from .ui import search_context

def listing(request, user, errormsg, context, tags_data):
    '''
    Listing framework.
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
    action_button = context['action_button']
    # Any action button to be displayed.
    # (action button)
    list_actions = context['list_actions']
    # Any list actions to the shown.
    # (list actions)

    try:
        items_searched, search = search_context_obj(request, search_object)
    except (KeyError, ValueError):
        items_searched, search = None, None

    item_list = item_list_object(items_searched)

    '''
    try:
        sort_terms = request.query['order_by']
    except KeyError:
        pass
    else:
        item_list = item_list.select().order_by(
            getattr(Page, sort_terms).asc()
            )
    '''

    paginator, rowset = utils.generate_paginator(item_list, request)

    tags = template_tags(
        search=search,
        user=user,
        **tags_data
        )

    tags.status = errormsg if errormsg is not None else None

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context[search_ui], search_object),
        menu=generate_menu(menu, search_object),
        rowset=rowset,
        colset=colsets[colset],
        icons=icons,
        action=action_button,
        list_actions=list_actions,
        **tags.__dict__)

    return tpl
