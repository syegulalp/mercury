from core import (auth)
from core.menu import generate_menu
from core.models import (Blog, Media,
    template_tags, Page, Tag)
from core.models.transaction import transaction
from core.libs.bottle import (template, request)
from core.search import tag_search_results, tag_in_blog_search_results
from . import search_context, listing
from core.utils import url_unescape, Status

def tag_recently_modified(tag):
    import datetime
    recent_pages = tag.pages.where(Page.modified_date > datetime.datetime.utcnow() - datetime.timedelta(hours=1))
    recent_count = recent_pages.count()
    if recent_count > 0:
        return 'There are {} pages using this tag that have been modified in the past hour. It is not recommended that you change this tag.'.format(recent_count)
    else:
        return None

@transaction
def tags_list(blog_id):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_author(user, blog)

    reason = auth.check_tag_editing_lock(blog, True)

    return listing(
        request, user, None,
        {
            'colset':'tags',
            'menu':'blog_manage_tags',
            'search_ui':'blog_tags',
            'search_object':blog,
            'search_context':tag_search_results,
            'item_list_object':blog.tags
        },
        {'blog_id':blog.id,
            'status':reason}
        )

@transaction
def tag_edit(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_editor(user, blog)

    auth.check_tag_editing_lock(blog)

    try:
        tag = Tag.get(Tag.id == tag_id,
                      Tag.blog == blog_id)
    except Tag.DoesNotExist:
        raise Tag.DoesNotExist("No such tag #{} in blog {}.".format(
            tag_id,
            blog.for_log))

    tags = template_tags(
        user=user)

    from core.utils import html_escape

    if request.method == "POST":

        new_tag_name = request.forms.getunicode('tag_name')
        if new_tag_name != tag.tag:

            try:
                Tag.get(Tag.tag == new_tag_name)

            except Tag.DoesNotExist:
                tag_count = tag.pages.count()

                msg = "Tag changed from {} to <b>{}</b>. {} pages (and their archives) have been queued for republishing.".format(
                    tag.for_log,
                    html_escape(new_tag_name),
                    tag_count)

                tag.tag = new_tag_name
                tag.save()

                if tag_count > 0:

                    from core.cms import queue
                    from core.models import db

                    with db.atomic() as txn:

                        queue.queue_page_actions(tag.pages.published)
                        queue.queue_ssi_actions(blog)
                        queue.queue_index_actions(blog, True)

                tags.status = Status(
                    type='info',
                    message=msg
                    )

            else:

                msg = "Tag not renamed. A tag with the name '{}' already exists.".format(
                    html_escape(new_tag_name)
                )

                tags.status = Status(
                    type='danger',
                    message=msg,
                    no_sure=True)
    else:
        tag_modified = tag_recently_modified(tag)
        if tag_modified:
            tags.status = Status(
                    type='danger',
                    message=tag_modified,
                    no_sure=True)

    tpl = template('edit/tag',
        menu=generate_menu('blog_edit_tag', tag),
        search_context=(search_context['sites'], None),
        tag=tag,
        **tags.__dict__)

    return tpl

@transaction
def tag_delete(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_publisher(user, blog)

    auth.check_tag_editing_lock(blog)

    try:
        tag = Tag.get(Tag.id == tag_id,
                      Tag.blog == blog_id)
    except Tag.DoesNotExist:
        raise Tag.DoesNotExist("No such tag #{} in blog {}.".format(
            tag_id,
            blog.for_log))

    from settings import BASE_URL
    tag_page_count = tag.pages.count()

    if request.forms.getunicode('confirm') == user.logout_nonce:

        from core.models import db

        if tag_page_count > 0:
            p_count = tag.pages.published.count()

            from core.cms import queue

            with db.atomic() as txn:
                queue.queue_page_actions(tag.pages.published)
                queue.queue_ssi_actions(blog)
                queue.queue_index_actions(blog, True)

            recommendation = '''
<p><b>{}</b> pages affected by this change have been pushed to the queue.</p>
'''.format(p_count)
        else:
            recommendation = '''
<p>No pages were associated with this tag.</p>
'''
        with db.atomic() as txn:
            tag.delete_instance(recursive=True)

        status = Status(
            type='success',
            close=False,
            message='''
Tag <b>{}</b> was successfully deleted from blog <b>{}</b>.</p>{}
'''.format(tag.for_log, blog.for_display, recommendation)
            )

    else:

        if tag_page_count > 0:
            recommendation = '''
<p><b>There are still <a target="_blank" href="{}/blog/{}/tag/{}/pages">{} pages</a> associated with this tag.</b></p>
'''.format(BASE_URL, blog.id, tag.id, tag_page_count)

            tag_modified = tag_recently_modified(tag)
            if tag_modified:
                recommendation += "<p><b>" + tag_modified + "</b></p>"

        else:
            recommendation = ''

        status = Status(
                type='warning',
                close=False,
                message='''
    You are about to delete tag <b>{}</b> in blog <b>{}</b>.</p>{}
    '''.format(tag.for_listing, blog.for_display, recommendation),
                url='{}/blog/{}/tag/{}/delete'.format(
                    BASE_URL, blog.id, tag.id),
                yes={'id':'delete',
                    'name':'confirm',
                    'label':'Yes, I want to delete this tag',
                    'value':user.logout_nonce},
                no={'label':'No, don\'t delete this tag',
                    'url':'{}/blog/{}/tag/{}'.format(
                    BASE_URL, blog.id, tag.id)}
                )

    tags = template_tags(
        user=user)
    tags.status = status

    tpl = template('listing/report',
        menu=generate_menu('blog_delete_tag', tag),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def tag_get(blog_id, tag_name):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_member(user, blog)

    tag_name = url_unescape(tag_name)

    tag_list = Tag.select().where(
        Tag.tag.contains(tag_name),
        Tag.blog == blog)

    import json
    tag_list_json = json.dumps([{'tag':t.tag,
                                'id':t.id} for t in tag_list])

    return tag_list_json

@transaction
def tags_get(blog_id, limit, page_limit):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_member(user, blog)

    from core.models import TagAssociation

    blog_pages = blog.pages.published.select(Page.id).order_by(Page.publication_date.desc()).limit(page_limit)
    tag_assc = TagAssociation.select(TagAssociation.tag).where(TagAssociation.page << blog_pages)
    tag_list = Tag.select(Tag.tag, Tag.id).where(Tag.id << tag_assc)

    # tag_list = Blog.load(blog_id).tags_all.order_by(Tag.id.desc())

    if limit:
        tag_list = tag_list.limit(limit)

    import json
    tag_list_json = json.dumps([{'tag':t.tag,
                                'id':t.id} for t in tag_list])
    return tag_list_json

@transaction
def tag_make_for_media(media_id=None, tag=None):

    user = auth.is_logged_in(request)
    media = Media.load(media_id)
    permission = auth.is_media_owner(user, media)

    if tag == None:
        tag_name = request.forms.getunicode('tag')
    else:
        tag_name = tag

    if len(tag_name) < 1:
        return None

    # Note that this is a single tag only!

    tag = Tag.add_or_create((tag_name,),
        media=media)

    if len(tag[0]) > 0:
        tpl = template(tag[0][0].new_tag_for_display)
    else:
        tpl = template(tag[1][0].for_display)

    return tpl


@transaction
def tag_make_for_page(blog_id=None, page_id=None):

    user = auth.is_logged_in(request)

    if page_id is None:
        # page = Page()
        blog = Blog.load(blog_id)
        page = None
        permission = auth.is_blog_editor(user, blog)
        assoc = {'blog':blog}
    else:
        page = Page.load(page_id)
        blog = None
        permission = auth.is_page_editor(user, page)
        assoc = {'page':page}

    tag_name = request.forms.getunicode('tag')

    if len(tag_name) < 1:
        return None

    # Note that this is a single tag only!

    tag = Tag.add_or_create(
        [tag_name, ],
        **assoc
        )

    if len(tag[0]) > 0:
        tpl = template(tag[0][0].new_tag_for_display)
    else:
        tpl = template(tag[1][0].for_display)

    return tpl

@transaction
def tag_list_pages(blog_id, tag_id):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_member(user, blog)
    tag = Tag.load(tag_id)

    return listing(
        request, user, None,
        {
            'colset':'blog',
            'menu':'blog_pages_for_tag',
            'search_ui':'blog_pages_with_tag',
            'search_object':tag,
            'search_context':tag_in_blog_search_results,
            'item_list_object':tag.pages.order_by(Page.publication_date.desc()),
            # 'action_button':action,
            # 'list_actions':list_actions
        },
        {'blog_id':blog.id}
        )
