from core import auth
from core.search import site_search_results
from core.models import Site
from core.models.transaction import transaction
from core.libs.bottle import request
from . import listing

@transaction
def site(site_id, errormsg=None):
    '''
    UI for listing contents of a given site
    '''
    user = auth.is_logged_in(request)
    site = Site.load(site_id)
    permission = auth.is_site_member(user, site)

    return listing(request, site, site.blogs.select(),
                   'site', 'site_menu',
                   user=user,
                   search_ui='site',
                   search_context=site_search_results,
                   errormsg=errormsg,
                   tags_data={'site':site}
                   )
