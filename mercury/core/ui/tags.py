from core import (auth)
from core.menu import generate_menu
from core.models import (Blog, Media,
    template_tags, Page, Tag)
from core.models.transaction import transaction
from core.libs.bottle import (template, request)
from . import search_context
import json
from core.utils import url_unescape

@transaction
def edit_tag(blog_id, tag_id):
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

    from core.utils import html_escape, Status

    if request.method == "POST":

        new_tag_name = request.forms.getunicode('tag_name')
        if new_tag_name != tag.tag:

            try:
                Tag.get(Tag.tag == new_tag_name)

            except Tag.DoesNotExist:
                msg = "Tag changed from {} to <b>{}</b>. {} pages (and their archives) have been queued for republishing.".format(
                    tag.for_log,
                    html_escape(new_tag_name),
                    tag.pages.count())

                tag.tag = new_tag_name
                tag.save()

                from core.cms import queue
                from core.models import page_status

                queue.queue_page_actions(tag.pages.where(Page.status == page_status.published))
                queue.queue_ssi_actions(blog)
                queue.queue_index_actions(blog)

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
        import datetime
        recent_pages = tag.pages.where(Page.modified_date > datetime.datetime.utcnow() - datetime.timedelta(hours=1))
        if recent_pages.count() > 0:
            tags.status = Status(
                    type='danger',
                    message='There are {} pages using this tag that have been modified in the past hour. It is not recommended that you change this tag.'.format(recent_pages.count()),
                    no_sure=True)

    tpl = template('edit/tag',
        menu=generate_menu('blog_edit_tag', tag),
        search_context=(search_context['sites'], None),
        tag=tag,
        **tags.__dict__)

    return tpl

@transaction
def get_tag(blog_id, tag_name):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_member(user, blog)

    tag_name = url_unescape(tag_name)

    tag_list = Tag.select().where(
        Tag.tag.contains(tag_name),
        Tag.blog == blog)

    tag_list_json = json.dumps([{'tag':t.tag,
                                'id':t.id} for t in tag_list])

    return tag_list_json

@transaction
def get_tags(blog_id, limit, page_limit):

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
def make_tag_for_media(media_id=None, tag=None):

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
def make_tag_for_page(blog_id=None, page_id=None):

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

