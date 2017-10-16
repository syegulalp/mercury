from core import (auth, utils)
from core.ui import sidebar
from core.log import logger
from core.menu import generate_menu, icons
from core.search import media_search_results

from core.models import (Struct,
    template_tags, Page, Blog, Media)

from core.models.transaction import transaction

from core.libs.bottle import (template, request)

from settings import BASE_URL

from . import listing, status_badge, search_context

@transaction
def media_list(blog_id):
    '''
    UI for listing media for a given blog
    '''

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_member(user, blog)

    return listing(
        request, user, None,
        {
            'colset':'media',
            'menu':'blog_manage_media',
            'search_ui':'blog_media',
            'search_object':blog,
            'search_context':media_search_results,
            'item_list_object':blog.media.order_by(Media.id.desc())
        },
        {'blog_id':blog.id}
        )

@transaction
def media_edit(blog_id, media_id, status=None):
    '''
    UI for editing a given media entry
    '''
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = Media.load(media_id, blog)
    permission = auth.is_media_owner(user, media)

    from core.ui import kv
    kv_ui_data = kv.ui(media.kv_list())

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user,
        )
    tags.sidebar = sidebar.render_sidebar(
            panel_set='edit_media',
            status_badge=status_badge,
            kv_object='Media',
            kv_objectid=media.id,
            kv_ui=kv_ui_data)

    return media_edit_output(tags)

@transaction
def media_edit_save(blog_id, media_id):
    '''
    Save changes to a media entry.
    '''
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = Media.load(media_id)
    permission = auth.is_media_owner(user, media)

    friendly_name = request.forms.getunicode('media_friendly_name')

    changes = False

    if friendly_name != media.friendly_name:
        changes = True
        media.friendly_name = friendly_name

    import datetime

    if changes is True:
        media.modified_date = datetime.datetime.utcnow()
        media.save()

        status = utils.Status(
            type='success',
            message='Changes to media <b>{}</b> saved successfully.'.format(
                media.for_display)
            )
    else:

        status = utils.Status(
            type='warning',
            no_sure=True,
            message='No discernible changes submitted for media <b>{}</b>.'.format(
                media.id, media.for_display)
            )

    logger.info("Media {} edited by user {}.".format(
        media.for_log,
        user.for_log))

    from core.ui import kv
    kv_ui_data = kv.ui(media.kv_list())

    tags = template_tags(blog_id=blog.id,
         media=media,
         status=status,
         user=user)

    tags.sidebar = sidebar.render_sidebar(
        panel_set='edit_media',
        status_badge=status_badge,
        kv_object='Media',
        kv_objectid=media.id,
        kv_ui=kv_ui_data)

    return media_edit_output(tags)

def media_edit_output(tags):

    return template('edit/media',
        icons=icons,
        menu=generate_menu('blog_edit_media', tags.media),
        search_context=(search_context['blog_media'], tags.blog),
        **tags.__dict__)

def media_pages(blog_id, media_id):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = Media.load(media_id, blog)

    return listing(
        request, user, None,
        {
            'colset':'blog',
            'menu':'blog_media_pages',
            'search_ui':'blog_media_pages',
            'search_object':media,
            'search_context': media_search_results,
            'item_list_object':media.pages.order_by(Page.publication_date.desc()),

            # 'action_button':action,
            # 'list_actions':list_actions
        },
        {'blog_id':blog.id}
        )


        # 'colset':'blog',
        # 'menu':'blog_pages_for_tag',
        # 'search_ui':'blog_pages_with_tag',
        # 'search_object':tag,
        # 'search_context':tag_in_blog_search_results,
        # 'item_list_object':tag.pages.order_by(Page.publication_date.desc()),

# TODO: be able to process multiple media at once via a list
# using the list framework
# also allows for actions like de-associate, etc.
# any delete action that works with an attached asset, like a tag, should also behave this way
@transaction
def media_delete(blog_id, media_id, confirm='N'):

    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    is_member = auth.is_blog_member(user, blog)
    media = Media.load(media_id, blog)
    permission = auth.is_media_owner(user, media)

    tags = template_tags(blog_id=blog.id,
        media=media,
        user=user)

    report = []

    from core.utils import Status

    if request.forms.getunicode('confirm') == user.logout_nonce:

        from os import remove

        try:
            remove(media.path)
        except:
            pass

        media.delete_instance(recursive=True,
            delete_nullable=True)

        confirmed = Struct()
        confirmed.message = 'Media {} successfully deleted'.format(
            media.for_log)
        confirmed.url = '{}/blog/{}/media'.format(BASE_URL, blog.id)
        confirmed.action = 'Return to the media listing'

        tags.status = Status(
            type='success',
            message=confirmed.message,
            action=confirmed.action,
            url=confirmed.url,
            close=False)

    else:
        s1 = ('You are about to delete media object <b>{}</b> from blog <b>{}</b>.'.format(
            media.for_display,
            blog.for_display))

#         used_in = []
#
#         for n in media.pages:
#             used_in.append("<li>{}</li>".format(n.for_display))

        media_page_count = media.pages.count()

        if media_page_count > 0:

            s2 = '''
<p><b>There are still <a target="_blank" href="{}/blog/{}/media/{}/pages">{} pages</a> associated with this tag.</b></p>
<p>Deleting the object will remove it from these pages as well.</p>
<p>Any references to these images in text will show as broken.</p>
'''.format(BASE_URL, blog.id, media.id, media_page_count)

        else:
            s2 = '''
<p>This media object is not currently used in any pages.</p>
<p>However, if it is linked directly in a page without a media reference, any such links will break.</p>
'''

        yes = {
            'label':'Yes, delete this media',
            'id':'delete',
            'name':'confirm',
            'value':user.logout_nonce
            }
        no = {
            'label':'No, return to media properties',
            'url':'../{}/edit'.format(media.id)
            }

        tags.status = Status(
            type='warning',
            close=False,
            message=s1 + '<hr>' + s2,
            yes=yes,
            no=no
            )

    return template('listing/report',
        menu=generate_menu('blog_delete_media', media),
        icons=icons,
        report=report,
        search_context=(search_context['blog_media'], blog),
        msg_float=False,
        **tags.__dict__)

