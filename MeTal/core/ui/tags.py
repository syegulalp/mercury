from core import (auth)
from core.menu import generate_menu
from core.models import (Blog, Media,
    template_tags, Page, Tag)
from core.models.transaction import transaction
from core.libs.bottle import (template, request)
from . import search_context
import json

@transaction
def edit_tag(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_editor(user, blog)

    auth.check_tag_editing_lock(blog)

    try:
        tag = Tag.get(Tag.id == tag_id)
    except Tag.DoesNotExist:
        raise Tag.DoesNotExist("No such tag #{} in blog {}.".format(
            tag_id,
            blog.for_log))

    if request.method == "POST":
        pass
        # change tag
        # get list of all assets with changed tag
        # provide link
        # need to build search by tag ID

    tags = template_tags(
        user=user)

    tpl = template('edit/edit_tag_ui',
        menu=generate_menu('blog_edit_tag', tag),
        search_context=(search_context['sites'], None),
        tag=tag,
        **tags.__dict__)

    return tpl

@transaction
def get_tag(tag_name):

    tag_list = Tag.select().where(
        Tag.tag.contains(tag_name))

    try:
        blog = request.query['blog']
    except KeyError:
        blog = None

    if blog:
        tag_list = tag_list.select().where(Tag.blog == blog)

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

    '''
    try:
        tag = Tag.get(Tag.tag == tag_name,
            Tag.blog == media.blog)
    except Tag.DoesNotExist:
        new_tag = Tag(tag=tag_name,
            blog=media.blog)
        tpl = template(new_tag.new_tag_for_display)

    else:
        tpl = template(tag.for_display)
    '''


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

    '''
    # TODO: replace with add_or_create
    try:
        tag = Tag.get(Tag.tag == tag_name,
            Tag.blog == blog)
    except Tag.DoesNotExist:
        new_tag = Tag(tag=tag_name,
            blog=blog)
        tpl = template(new_tag.new_tag_for_display)

    else:
        tpl = template(tag.for_display)

    return tpl
    '''


