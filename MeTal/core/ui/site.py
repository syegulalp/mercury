from core import (auth, utils)
from core.menu import generate_menu, colsets, icons
from core.search import site_search_results

from core.models import (get_site, template_tags)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)

from .ui import search_context

@transaction
def site(site_id, errormsg=None):
    '''
    UI for listing contents of a given site
    '''
    user = auth.is_logged_in(request)
    site = get_site(site_id)
    permission = auth.is_site_member(user, site)

    try:
        blogs_searched, search = site_search_results(request, site)
    except (KeyError, ValueError):
        blogs_searched, search = None, None

    # page = utils.page_list_id(request)

    tags = template_tags(site_id=site.id,
        search=search,
        user=user)

    if errormsg is not None:
        tags.status = errormsg

    taglist = tags.site.blogs

    paginator, rowset = utils.generate_paginator(taglist, request)

    tpl = template('listing/listing_ui',
        paginator=paginator,
        search_context=(search_context['site'], site),
        menu=generate_menu('site_menu', site),
        rowset=rowset,
        colset=colsets['site'],
        icons=icons,
        **tags.__dict__)

    return tpl
