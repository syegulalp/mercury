from core import (auth, utils)
from core.menu import generate_menu, colsets, icons
from core.search import site_search_results

from core.models import (Site, template_tags)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)

from .ui import search_context

from . import listing

@transaction
def site(site_id, errormsg=None):
    '''
    UI for listing contents of a given site
    '''
    user = auth.is_logged_in(request)
    site = Site.load(site_id)
    permission = auth.is_site_member(user, site)

    return listing(
        request, user, errormsg,
        {
            'colset':'site',
            'menu':'site_menu',
            'search_ui':'site',
            'search_object':site,
            'search_context':site_search_results,
            'item_list_object':site.blogs.select(),
            # 'action_button':action,
            # 'list_actions':list_actions
        },
        {'site_id':site.id}
        )

