import datetime, time

from core.utils import (create_basename, Status, DATE_FORMAT)
from core.error import (PageNotChanged, DeletionError,)
from core.libs.bottle import request

from core.models import (Page, TagAssociation, Tag,
    Category, PageCategory, template_tags, page_status)

from . import save_action_list, invalidate_cache
from .queue import queue_page_actions, queue_ssi_actions, queue_index_actions, queue_page_archive_actions
from .fileinfo import (delete_page_fileinfo, build_archives_fileinfos, build_pages_fileinfos, delete_fileinfo_files,
                       purge_fileinfos, build_indexes_fileinfos)

from settings import BASE_URL

def save_page(page, user, blog=None):
    '''
    Saves edits to a page in the CMS.
    Note that this function does _not_ perform permission checking. In other words, it doesn't
    verify if the user described in the `user` parameter does in fact have permissions to
    edit the page in question.

    :param page:
        Page object whose data is to be saved. If this is None, then it is assumed that we are
        creating a new page.
    :param user:
        The user object associated with the save action for this page. If this is a newly-created page,
        the page's user will be set to this.
    :param blog:
        The blog object under which the page will be created, if this is a newly-created page.

    '''

    getunicode = request.forms.getunicode

    invalidate_cache()

    save_action = int(request.forms.get('save'))

    original_page_status = page_status.unpublished
    new_basename = getunicode('basename')

    if page is None:

        # CREATE NEW PAGE ENTRY

        page = Page()
        page.user = user.id
        page.blog = blog.id

        page.basename = create_basename(getunicode('page_title'),
            page.blog)
        original_page_basename = page.basename

        time_now = datetime.datetime.utcnow()

        page.publication_date = time_now
        page.created_date = time_now

    else:

        # UPDATE EXISTING ENTRY

        # Queue neighbor actions for page BEFORE modification

        if page.status == page_status.published:
            if not (save_action & save_action_list.UNPUBLISH_PAGE):
                queue_page_actions((page.next_page, page.previous_page))
                queue_page_archive_actions(page)

        original_page_status = page.status
        original_page_basename = page.basename

        page.modified_date = datetime.datetime.utcnow()

        change_basename = False

        if new_basename is not None:
            if new_basename == "":
                change_basename = True
                new_basename = create_basename(getunicode('page_title'),
                    page.blog)
            if new_basename != original_page_basename:
                change_basename = True

        new_publication_date = datetime.datetime.strptime(
            request.forms.get('publication_date'), DATE_FORMAT)

        if change_basename:
            page.basename = create_basename(new_basename, page.blog)

        page.publication_date = page._date_to_utc(page.blog.timezone, new_publication_date).replace(tzinfo=None)

        delete_page_fileinfo(page)

    page.title = getunicode('page_title')
    page.text = getunicode('page_text')
    page.status = page_status.modes[int(request.forms.get('publication_status'))]
    page.tag_text = getunicode('page_tag_text')
    page.excerpt = getunicode('page_excerpt')

    change_note = getunicode('change_note')

    msg = []

    # UNPUBLISH

    if (
        (save_action & save_action_list.UNPUBLISH_PAGE and page.status == page_status.published) or  # unpublished a published page
        (original_page_status == page_status.published and page.status == page_status.unpublished)  # set a published page to draft
        ):

        unpublish_page(page)
        msg.append("Page <b>{}</b> unpublished successfully.")


    # SET UNPUBLISHED TO PUBLISHED

    elif original_page_status == page_status.unpublished and (save_action & save_action_list.UPDATE_LIVE_PAGE):
        page.status = page_status.published
        msg.append("Set to publish.")

    # SAVE DRAFT

    if (save_action & save_action_list.SAVE_TO_DRAFT):

        try:
            save_result = page.save(user, False, False, change_note)
        except PageNotChanged:
            save_result = (None, None)

        msg.append("Page <b>{}</b> saved successfully.")

        # Assign categories for page

        categories = []

        for n in request.forms.allitems():
            if n[0][:8] == 'cat-sel-':
                try:
                    category_id = int(n[0][8:])
                except ValueError:
                    category_id = None
                else:
                    categories.append(category_id)

        if not categories:
            categories.append(blog.default_category.id)
            msg.append(" Default category auto-assigned for page.")

        page_categories = []

        primary = None

        for n in page.categories:
            if n.category.id not in categories:
                delete_category = PageCategory.delete().where(
                    PageCategory.id == n.id)
                delete_category.execute()
            else:
                page_categories.append(n.category.id)
                if n.primary is True:
                    primary = n

        for n in categories:
            if n not in page_categories:
                new_page_category = PageCategory.create(
                    page=page,
                    category=Category.load(n, blog_id=page.blog.id),
                    primary=False)

        if primary is None:
            n = page.categories[0]
            n.primary = True
            n.save()

        build_archives_fileinfos((page,))
        build_pages_fileinfos((page,))

    # UPDATE TAGS

    if getunicode('tag_text') is not None:
        import json
        tag_text = json.loads(getunicode('tag_text'))
        add_tags_to_page(tag_text, page)
        delete_orphaned_tags(page.blog)

    # QUEUE CHANGES FOR PUBLICATION (if any)

    if ((save_action & save_action_list.UPDATE_LIVE_PAGE)
        and (page.status == page_status.published)):

        queue_ssi_actions(page.blog)
        queue_page_actions((page,))
        queue_index_actions(page.blog)

        msg.append(" Live page updated.")

    # DETECT ANY PAGE CHANGES

    if (
        (save_action & (save_action_list.SAVE_TO_DRAFT + save_action_list.UPDATE_LIVE_PAGE))
        and (save_result[1]) is None):

        msg.append(" (Page unchanged.)")

    # RETURN REPORT

    tags = template_tags(page=page, user=user)

    status = Status(
        type='success',
        message=' / '.join(msg),
        vals=(page.for_log,)
        )

    tags.status = status
    tags._save_action = save_action
    tags._save_action_list = save_action_list

    return tags

# TODO: Move this to the Blog or Tags methods.
# Maybe both by way of a proxy

def delete_orphaned_tags(blog):
    '''
    Cleans up tags that no longer have any page associations.

    :param blog:
        A blog object used as the context for this cleanup.
    '''
    orphaned_tags = Tag.delete().where(
        Tag.blog == blog,
        ~ Tag.id << (TagAssociation.select(TagAssociation.tag)))

    orphaned_tags.execute()

    return orphaned_tags

def add_tags_to_page (tag_text, page, no_delete=False):
    '''
    Takes a list of tags, in JSON text format, and adds them to the page in question.
    Any tags not already in the system will be added.

    :param tag_text:
        List of tags to add.
    :param page:
        Page object to add the tags to.
    :param no_delete:
        When set to True, this will preserve tags already in the page if they are
        not found in tag_text. By default this is False, so any tags not specified in
        tag_text that exist in the page will be removed.
    '''
    tag_list = Tag.select().where(Tag.id << tag_text)

    if no_delete is False:

        tags_to_delete = TagAssociation.delete().where(
            TagAssociation.page == page,
            ~ TagAssociation.tag << (tag_list))

        tags_to_delete.execute()
    else:
        tags_to_delete = None

    tags_in_page = page.tags_all.select(Tag.id).tuples()

    tags_to_add = tag_list.select().where(~Tag.id << (tags_in_page))

    for n in tags_to_add:
        add_tag = TagAssociation(
           tag=n,
           page=page)

        add_tag.save()

    import json
    new_tags = json.loads(request.forms.getunicode('new_tags'))

    for n in new_tags:
        if n != '':
            new_tag = Tag(
                tag=n,
                blog=page.blog)
            new_tag.save()

            add_tag = TagAssociation(
                tag=new_tag,
                page=page)

            add_tag.save()

    return tags_to_add, tags_to_delete, new_tags



def delete_page(page):
    '''
    Removes all database entries for a given page from the system.
    Implies an unpublish action.

    :param page:
        The page object to remove from disk.
    '''
    # TODO: make this part of the delete action for the schema
    # same with unpublish

    if page.status != page_status.unpublished:
        raise DeletionError('Page must be unpublished before it can be deleted')

    unpublish_page(page, save=False)
    # TODO: Move this into page.delete_instance, override by way of BaseModel
    # page.kv_del()
    delete_page_fileinfo(page)
    page.delete_instance(recursive=True)

    delete_orphaned_tags(page.blog)


def unpublish_page(page, save=True):
    '''
    Removes all the physical files associated with a given page,
    and queues any neighboring files to be republished.

    :param page:
        The page object to unpublish.
    :param no_save:
        By default the page object in question is saved before
        being unpublished. Set this to True to skip this step.
    '''
    page.status = page_status.unpublished

    if save:
        page.save(page.user)

    queue_page_actions((page.next_page, page.previous_page,), no_neighbors=True)
    queue_page_archive_actions(page)
    queue_index_actions(page.blog)

    delete_fileinfo_files(page.fileinfos)

def publish_page(page_id):
    '''
    Stub for the future republish_page function

    - test for presence of fileinfo
    - if not, create it (this is a precaution more than anything else)
    - build the page itself
    - build all the associated archive templates for that page only

        note: we might want to break that into a separately invoked function
        for the sake of queue optimization, so that multiple such indices
        can be coalesced effectively

    '''
    pass

# OBSOLETE - delete?
def publish_site(site_id):
    '''
    Stub for the future republish_site function
    loop through all blogs, run republish_blog on each
    '''
    pass

# OBSOLETE - delete?
def publish_blog(blog_id):
    '''
    stub
    loop through all pages, publish
    eventually a rewrite of republish_blog below, or just a rebadging
    '''
    pass

def republish_blog(blog):
    '''
    Queues all published pages and index items for a given blog.

    :param blog:
        The blog object to republish.
    '''

    data = []
    data.extend(["<h3>Queuing <b>{}</b> for republishing</h3><hr>".format(
        blog.for_log)])

    begin = time.clock()

    queue_ssi_actions(blog)
    queue_page_actions(blog.pages.published.iterator(), no_neighbors=True)
    queue_index_actions(blog, include_manual=True)

    end = time.clock()

    data.append("Total processing time: {0:.2f} seconds.".format(end - begin))
    data.append("<hr/><a href='{}/blog/{}/publish'>Click here to activate the publishing queue.</a>".format(
        BASE_URL,
        blog.id))
    return data


def purge_blog(blog):
    '''
    Deletes all fileinfos from a given blog and recreates them.
    This function may also eventually be expanded to delete all the files
    associated with a given blog (except for assets)
    No security checks are performed.

    Eventually we will make each of these purge and append actions
    into queueable behaviors, so that these operations don't time out.

    '''

    report = []
    report.append("<h3>Purging/Recreating <b>{}</b></h3>".format(blog.for_log))

    begin = time.clock()

    fileinfos_purged, fileinfocontexts_purged = purge_fileinfos(blog.fileinfos)

    erase = time.clock()

    report.append("<hr/>{0} fileinfo objects (and {1} fileinfo context objects) erased in {2:.2f} seconds.".format(
        fileinfos_purged,
        fileinfocontexts_purged,
        erase - begin
        ))

    includes_to_insert = blog.ssi_templates
    includes_inserted = build_indexes_fileinfos(includes_to_insert)

    ssi_time = time.clock()

    report.append("<hr/>{0} server-side include objects created in {1:.2f} seconds.".format(
        includes_inserted, ssi_time - erase))


    # pages_inserted = build_pages_fileinfos(blog.pages)
    pages_inserted = 0
    rebuild = time.clock()

    report.append("<hr/>{0} page objects created in {1:.2f} seconds,".format(pages_inserted,
        rebuild - erase))

    # f_i = build_archives_fileinfos(blog.published_pages)
    f_i = 0
    arch_obj = time.clock()
    report.append("{0} archive page objects created in {1:.2f} seconds.".format(f_i,
        arch_obj - rebuild))

    index_objects = build_indexes_fileinfos(blog.index_templates)
    index_obj = time.clock()
    report.append("{0} index page objects created in {1:.2f} seconds.".format(index_objects,
        index_obj - arch_obj))

    end = time.clock()

    total_objects = blog.pages.count() + f_i + blog.index_templates.count()
    report.append("<hr/>Total objects created: <b>{}</b>.".format(total_objects))
    report.append("Total processing time: <b>{0:.2f}</b> seconds.".format(end - begin))
    report.append("<hr/>It is recommended that you <a href='{}'>republish this blog</a>.".format(
        '{}/blog/{}/republish'.format(BASE_URL, blog.id)))


    return report

