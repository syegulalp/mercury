from core.utils import utf8_escape
from settings import DB


def blog_pages_in_category_search_results(request, category):
    return blog_search_results(request, category.blog)


def tag_in_blog_search_results(request, tag):
    return blog_search_results(request, tag.blog)


def media_in_blog_search_results(request, media):
    return blog_search_results(request, media.blog)


def blog_search_results(request, blog=None):

    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')

    if search_terms == "":
        raise ValueError('Search field is empty.')

    search_terms_enc = utf8_escape(search_terms)
    pages_searched = DB.blog_search(search_terms_enc, blog)

    return pages_searched, search_terms


def site_search_results(request, site=None):

    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')

    if search_terms == "":
        raise ValueError('Search field is empty.')

    search_terms_enc = utf8_escape(search_terms)
    pages_searched = DB.site_search(search_terms_enc, site)

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

    from core.models import Media

    # TODO: move to DB.media_search for indexing

    media_searched = (Media.select(Media.id)
        .where(Media.friendly_name.contains(search_terms_enc) |
            Media.filename.contains(search_terms_enc))
        .order_by(Media.id.desc()).tuples())

    if site_id is not None:
        media_searched.select().where(Media.site == site_id)
    if blog_id is not None:
        media_searched.select().where(Media.blog == blog_id)

    return media_searched, search_terms


def tag_search_results(request, blog_id=None, site_id=None):

    try:
        search_terms = request.query['search']
    except KeyError:
        raise KeyError('No search field in query.')

    if search_terms == "":
        raise ValueError('Search field is empty.')

    search_terms_enc = utf8_escape(search_terms)

    from core.models import Tag

    # TODO: move to DB.media_search for indexing

    tags_searched = (Tag.select(Tag.id)
        .where(Tag.tag.contains(search_terms_enc))
        .order_by(Tag.tag.asc()).tuples())

    # if site_id is not None:
        # tags_searched.select().where(Tag.blog.site == site_id)
    if blog_id is not None:
        tags_searched.select().where(Tag.blog == blog_id)

    return tags_searched, search_terms
