from core.utils import utf8_escape
from models import Page, get_site
from settings import DB

# TODO: merge these two 
def blog_search_results(request, blog=None):
        
    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')
    
    if search_terms == "":
        raise ValueError('Search field is empty.')
    
    search_terms_enc = utf8_escape(search_terms)
    pages_searched = DB.blog_search(search_terms_enc)
    
    if blog is not None:
        pages_searched = blog.pages(pages_searched).select(Page.id).tuples()
    
    return pages_searched, search_terms

def site_search_results(request, site_id=None):
        
    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')
    
    if search_terms == "":
        raise ValueError('Search field is empty.')
    
    search_terms_enc = utf8_escape(search_terms)
    pages_searched = DB.site_search(search_terms_enc)

    if site_id is not None:
        pages_searched = get_site(site_id).pages(pages_searched).select(Page.id).tuples()
    
    return pages_searched, search_terms

# placeholder function, not implemented yet

def media_search_results(request, blog_id=None, site_id=None):
    
    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')
    
    if search_terms == "":
        raise ValueError('Search field is empty.')
    
    search_terms_enc = utf8_escape(search_terms)
    
    # not working yet
    '''media_searched = (Page_Search.select(Page_Search.id)
        .where(Page_Search.title.contains(search_terms_enc) | Page_Search.text.contains(search_terms_enc))
        .order_by(Page_Search.id.desc()).tuples())
    '''
        
    if site_id is not None:
        pass  #        
    if blog_id is not None:
        pass  # pages_searched = get_blog(blog_id).media().select(Page.id).tuples()
    
    return None
    # return media_searched, search_terms