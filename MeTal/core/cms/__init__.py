import os, datetime

from core.utils import (create_basename, Status, generate_date_mapping, date_format, MetalTemplate)
from core.error import (ArchiveMappingFormatException, PageNotChanged, EmptyQueueError,
    QueueInProgressException, PageTemplateError, DeletionError, NoArchiveForFileInfo)
from core.log import logger
from core.auth import publishing_lock
from core.libs.bottle import request
from core.libs.peewee import DeleteQuery

from core.models import (db, Page, Template, TemplateMapping, TagAssociation, Tag, template_type,
    Category, PageCategory, FileInfo, template_tags, User, Blog, Site,
    FileInfoContext, Media, MediaAssociation, Struct, page_status, publishing_mode, Queue)

from settings import MAX_BATCH_OPS, BASE_URL
from core.libs.peewee import IntegrityError
import time

template_cache = {}
blog_tag_cache = {}

save_action_list = Struct()

save_action_list.SAVE_TO_DRAFT = 1
save_action_list.UPDATE_LIVE_PAGE = 2
save_action_list.EXIT_EDITOR = 4
save_action_list.UNPUBLISH_PAGE = 8
save_action_list.DELETE_PAGE = 16

job_type = Struct()
job_type.page = 'Page'
job_type.index = 'Index'
job_type.archive = 'Archive'
job_type.include = 'Include'
job_type.insert = 'Insert'
job_type.control = 'Control'

job_type.description = {
    job_type.page: 'Page entry',
    job_type.index: 'Index entry',
    job_type.archive: 'Archive entry',
    job_type.include: 'Include file',
    job_type.insert: 'Queue insert job',
    job_type.control: 'Queue publishing job'
    }

job_type.action = {
    job_type.page: lambda x:build_page(x),
    job_type.index: lambda x:build_page(x),
    job_type.archive: lambda x:build_page(x),
    job_type.include: lambda x:build_page(x),
    }

job_insert_type = Struct()

job_insert_type.page_fileinfo = "page_fileinfos"
job_insert_type.index_fileinfo = "index_fileinfos"
job_insert_type.ssi_fileinfo = "ssi_fileinfos"
job_insert_type.page = "page"
job_insert_type.index = "index"
job_insert_type.ssi = "ssi"


media_filetypes = Struct()
media_filetypes.image = "Image"
media_filetypes.types = {
    'jpg':media_filetypes.image,
    'gif':media_filetypes.image,
    'png':media_filetypes.image,
    }

def build_page(queue_entry):
    try:
        fileinfo = FileInfo.get(FileInfo.id == queue_entry.data_integer)
        blog = queue_entry.blog
        page_tags = generate_page_tags(fileinfo, blog)
        file_page_text = generate_page_text(fileinfo, page_tags)
        write_file(file_page_text, blog.path, fileinfo.file_path)

    except FileInfo.DoesNotExist as e:
        raise Exception('''Fileinfo {} could not be found in the system.
It may refer to a fileinfo that was deleted by another action. ({})'''.format(queue_entry.data_integer, e))

    except NoArchiveForFileInfo:
        logger.info("Fileinfo {} has no corresponding pages. File {} removed.".format(
            fileinfo.id,
            fileinfo.file_path)
            )
        delete_fileinfo_files((fileinfo,))
        # fileinfo.delete_instance(recursive=True)
        # FIXME: for now we leave this out
        # because deletes do not coalesce properly in the queue (I think)

    except Exception as e:
        context_list = [(f.object, f.ref) for f in fileinfo.context]
        raise Exception('Error building fileinfo {} ({},{},{}): {}'.format(
            fileinfo.id,
            fileinfo.page,
            context_list,
            fileinfo.file_path,
            e))


def write_file(file_text, blog_path, file_path):
    '''
    Builds a single file based on a fileinfo entry f for a given blog.
    Returns details about the built file.

    This does _not_ perform any checking for the page's publication status,
    nor does it perform any other higher-level security.

    This should be the action that is pushed to the queue, and consolidated
    based on the generated filename. (The consolidation should be part of the queue push function)

    :param f:
        The fileinfo object to use.
    :param blog:
        The blog object to use as the context for the fileinfo.
    '''

    file_pathname = blog_path + "/" + file_path

    encoded_page = file_text.encode('utf8')

    split_path = file_path.rsplit('/', 1)

    if len(split_path) > 1:
        path_to_check = blog_path + "/" + split_path[0]
    else:
        path_to_check = blog_path

    if os.path.isdir(path_to_check) is False:
        os.makedirs(path_to_check)

    with open(file_pathname, "wb") as output_file:
        output_file.write(encoded_page)

def generate_page_tags(f, blog):
    '''
    Returns the page text and the pathname for a file to generate.
    Used with build_file but can be used for other things as well.

    :param f:
        The fileinfo object to use.
    :param blog:
        The blog object to use as the context for the fileinfo.
    '''

    if f.page is None:

        if f.xref.template.template_type == template_type.index:
            tags = template_tags(blog=blog,
                fileinfo=f)
        else:

            archive_pages = generate_archive_context_from_fileinfo(
                f.xref.archive_xref, blog.published_pages, f)

            # The context object we use

            tags = template_tags(blog=blog,
                archive=archive_pages,
                archive_context=f,
                fileinfo=f)

    else:
        tags = template_tags(page=f.page,
            fileinfo=f)

    if tags.archive is not None:
        if tags.archive.pages.count() == 0:
            raise NoArchiveForFileInfo('No archives for page {} using fileinfo {}'.format(
            f.page, f))

    return tags
    # page_text = generate_page_text(f, tags)
    # return page_text

def push_to_queue(**ka):
    '''
    Inserts a single job item into the work queue.

    :param job_type:
        A string representing the type of job to be inserted.
        One of a list of strings from the job_type object in core.cms.

    :param data_integer:
        Any integer data passed along with the job. For a job control item, this
        is the number of items remaining for that particular job.
        For a regular publishing job, this is the id of the fileinfo.

    :param blog:
        The blog object associated with the job.

    :param site:
        The site object associated with the job.

    :param priority:
        An integer, from 0-9, representing the processing priority associated with the job.
        Higher-priority jobs are processed first. Most individual pages are given a high
        priority; indexes are lower.
    '''

    try:
        queue_job = Queue.get(
            Queue.job_type == ka['job_type'],
            Queue.data_integer == ka['data_integer'],
            Queue.blog == ka['blog'],
            Queue.site == ka['site']
            )
    except Queue.DoesNotExist:
        queue_job = Queue()
    else:
        return

    queue_job.job_type = ka['job_type']
    queue_job.data_integer = int(ka.get('data_integer', None))
    queue_job.blog = ka.get('blog', Blog()).id
    queue_job.site = ka.get('site', Site()).id
    queue_job.priority = ka.get('priority', 9)
    queue_job.is_control = ka.get('is_control', False)

    if queue_job.is_control:
        queue_job.data_string = ka.get('data_string', (queue_job.job_type + ": Blog {}".format(
            queue_job.blog.for_log)))
    else:
        queue_job.data_string = (queue_job.job_type + ": " +
            FileInfo.get(FileInfo.id == queue_job.data_integer).file_path)


    queue_job.date_touched = datetime.datetime.utcnow()
    queue_job.save()

def remove_from_queue(queue_deletes):
    '''
    Removes jobs from the queue.
    :param queue_deletes:
        A list of queue items, represented by their IDs, to be deleted.
    '''
    deletes = Queue.delete().where(Queue.id << queue_deletes)
    return deletes.execute()

def queue_page_actions(pages, no_neighbors=False, no_archive=False):
    '''
    Pushes a Page object along with all its related items into the queue for publication.
    This includes any archive indices associated with the page, and the page's next and
    previous entries in its respective categories.

    Note that this will only queue items that are actually set to be published.

    :param page:
        The Page object whose actions are to be queued.
    :param no_neighbors:
        Set to True to suppress generation of next/previous posts. Useful if you've loaded
        all the posts for a blog into a queue and don't need to have this performed here.
    :param no_archive:
        Set to True to suppress generation of archive pages associated with this page. Also
        useful for mass-queued actions.
    '''
    if pages is None:
        return

    for page in pages:

        try:

            fileinfos, blog, site = page.fileinfos, page.blog, page.blog.site

            for f in fileinfos:
                if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:
                    push_to_queue(job_type=job_type.page,
                        blog=blog,
                        site=site,
                        data_integer=f.id)

            if no_archive is False:
                queue_page_archive_actions(page)

            if no_neighbors is False:

                next_page = page.next_page
                previous_page = page.previous_page

                if next_page is not None:

                    fileinfos_next = next_page.fileinfos

                    for f in fileinfos_next:

                        if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:

                            push_to_queue(job_type=job_type.page,
                                blog=blog,
                                site=site,
                                data_integer=f.id)

                            queue_page_archive_actions(next_page)

                if previous_page is not None:

                    fileinfos_previous = previous_page.fileinfos

                    for f in fileinfos_previous:

                        if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:

                            push_to_queue(job_type=job_type.page,
                                blog=blog,
                                site=site,
                                data_integer=f.id)

                            queue_page_archive_actions(previous_page)

        except Exception as e:
            from core.error import QueueAddError
            raise QueueAddError('Page {} could not be queued: '.format(
                page.for_log,
                e))

def eval_paths(path_string, dict_data):
    path_string = replace_mapping_tags(path_string)
    try:
        paths = eval(path_string, dict_data)
    except Exception as e:
        paths = None
        # raise Exception('Invalid path string: {} // Data: {} // Exception: {}'.format(
            # path_string,
            # dict_data,
            # e))
    return paths

def queue_page_archive_actions(page):
    '''
    Pushes to the publishing queue all the page archives for a given page object.

    :param page:
        The page object whose archives will be pushed to the publishing queue.
    '''

    archive_templates = page.blog.archive_templates
    tags = template_tags(page=page)

    for n in archive_templates:
        try:
            if n.publishing_mode != publishing_mode.do_not_publish:
                for m in n.mappings:
                    path_list = eval_paths(m.path_string, tags.__dict__)
                    paths = []

                    if type(path_list) == list:
                        for pp in path_list:
                            paths.append(pp[1])
                    else:
                        paths.append(path_list)

                    for p in paths:
                        if p is None: continue
                        file_path = (page.blog.path + '/' +
                                     generate_date_mapping(
                                         page.publication_date_tz.date(),
                                         tags,
                                         p,
                                         do_eval=False))

                        # FIXME: We may not need this anymore

                        while 1:
                            try:
                                fileinfo_mapping = FileInfo.get(FileInfo.sitewide_file_path == file_path)
                            except FileInfo.DoesNotExist:
                                if build_archives_fileinfos((page,)) == 0:
                                    from core.error import QueueAddError
                                    raise QueueAddError(
                                        'No archive fileinfos could be built for page {} with template {}'.format(
                                        page.for_log,
                                        n.template.for_log))
                            else:
                                break


                        push_to_queue(job_type=job_type.archive,
                                  blog=page.blog,
                                  site=page.blog.site,
                                  data_integer=fileinfo_mapping.id)
        except Exception as e:
            from core.error import QueueAddError
            raise QueueAddError('Archive template {} for page {} could not be queued: '.format(
                n,
                page.for_log,
                e))



def queue_ssi_actions(blog):
    '''
    Pushes to the publishing queue all the SSIs for a given blog.

    :param blog:
        The blog object whose SSI templates will be pushed to the queue.
    '''

    templates = blog.ssi_templates.select()

    if templates.count() == 0:
        return None

    for n in templates:
        for f in n.fileinfos:
            push_to_queue(
                job_type=job_type.include,
                priority=10,
                blog=blog,
                site=blog.site,
                data_integer=f.id)

def queue_index_actions(blog, include_manual=False):
    '''
    Pushes to the publishing queue all the index pages for a given blog
    that are marked for Immediate publishing.

    :param blog:
        The blog object whose index templates will be pushed to the queue.
    :param include_manual:
        If set to True, all templates, including those set to the Manual publishing mode,
        will be pushed to the queue. Default is False, since those templates are not
        pushed in most publishing actions.
    '''

    templates = blog.index_templates.select().where(
        Template.publishing_mode != publishing_mode.do_not_publish)

    if include_manual is False:
        templates = templates.select().where(
            Template.publishing_mode == publishing_mode.immediate)

    if templates.count() == 0:
        raise Template.DoesNotExist("No valid index templates exist for blog {}.".format(
            blog.for_log))

    mappings = TemplateMapping.select().where(TemplateMapping.template << templates)

    fileinfos = FileInfo.select().where(FileInfo.template_mapping << mappings)

    for f in fileinfos:
        push_to_queue(job_type=job_type.index,
            priority=1,
            blog=blog,
            site=blog.site,
            data_integer=f.id)

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

    save_action = int(request.forms.get('save'))

    blog_new_page = False
    original_page_status = page_status.unpublished

    if page is None:

        blog_new_page = True

        page = Page()
        page.user = user.id
        page.blog = blog.id

        page.basename = create_basename(request.forms.getunicode('page_title'),
            page.blog)
        original_page_basename = page.basename

        page.publication_date = datetime.datetime.utcnow()
        page.created_date = datetime.datetime.utcnow()

    else:

        # Queue actions for page BEFORE modification

        if page.status == page_status.published and (save_action & save_action_list.UPDATE_LIVE_PAGE):
            queue_page_actions((page,))

        original_page_status = page.status
        original_page_basename = page.basename

        page.modified_date = datetime.datetime.utcnow()

        if request.forms.getunicode('basename') is not None:
            if request.forms.getunicode('basename') != "":
                if original_page_basename != request.forms.getunicode('basename'):
                    page.basename = create_basename(request.forms.getunicode('basename'),
                        page.blog)

            else:
                page.basename = create_basename(request.forms.getunicode('page_title'),
                    page.blog)

    if original_page_basename != page.basename:
        delete_page_fileinfo(page)

    if page.basename == "":
        page.basename = create_basename(request.forms.getunicode('page_title'),
            page.blog)
        original_page_basename = page.basename

    page.title = request.forms.getunicode('page_title')
    page.text = request.forms.getunicode('page_text')
    page.status = page_status.modes[int(request.forms.get('publication_status'))]

    from core.utils import DATE_FORMAT
    page.publication_date = datetime.datetime.strptime(
        request.forms.get('publication_date'), DATE_FORMAT)

    new_time = page._date_to_utc(
        page.blog.timezone, page.publication_date).replace(tzinfo=None)
    page.publication_date = new_time

    page.tag_text = request.forms.getunicode('page_tag_text')
    page.excerpt = request.forms.getunicode('page_excerpt')

    change_note = request.forms.getunicode('change_note')

    msg = []

    # DELETING PAGES IS NOT HANDLED HERE, SEE delete_page

    # UNPUBLISH
    if (
        (save_action & save_action_list.UNPUBLISH_PAGE and page.status == page_status.published) or  # unpublished a published page
        (original_page_status == page_status.published and page.status == page_status.unpublished)  # set a published page to draft
        ):

        unpublish_page(page)
        page.status = page_status.unpublished
        msg.append("Page <b>{}</b> unpublished successfully.")


    # UNPUBLISHED TO PUBLISHED
    if original_page_status == page_status.unpublished and (save_action & save_action_list.UPDATE_LIVE_PAGE):
        page.status = page_status.published
        msg.append("Set to publish.")

    # SAVE DRAFT
    if (save_action & save_action_list.SAVE_TO_DRAFT):

        # backup_only = True if request.forms.getunicode('backup') == "Y" else False
        try:
            save_result = page.save(user, False, False, change_note)
        except PageNotChanged:
            save_result = (None, None)

        msg.append("Page <b>{}</b> saved successfully.")

        if blog_new_page:

            # TODO: setting default category should be done on object creation

            saved_page_category = PageCategory.create(
                page=page,
                category=blog.default_category,
                primary=True)

        else:

            categories = []
            for n in request.forms.allitems():
                if n[0][:8] == 'cat-sel-':
                    try:
                        category_id = int(n[0][8:])
                    except ValueError:
                        category_id = None
                    else:
                        categories.append(category_id)

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

            if page.categories.count() == 0:
                default_page_category = PageCategory.create(
                    page=page,
                    category=Category.get(
                        blog=page.blog,
                        default=True)
                    )
                primary = default_page_category
                msg.append(" Default category auto-assigned for page.")

            if primary is None:
                n = page.categories[0]
                n.primary = True
                n.save()

    if request.forms.getunicode('tag_text') is not None:
        import json
        tag_text = json.loads(request.forms.getunicode('tag_text'))
        add_tags_to_page(tag_text, page)
        delete_orphaned_tags(page.blog)

    if ((save_action & save_action_list.UPDATE_LIVE_PAGE)
        and (page.status == page_status.published)):

        # BUILD FILEINFO IF NO DELETE ACTION

        # clear fileinfos?

        build_archives_fileinfos((page,))
        build_pages_fileinfos((page,))

        # QUEUE CHANGES FOR PUBLICATION

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

def add_page_fileinfo(page, template_mapping, file_path,
        url, sitewide_file_path, mapping_sort=None):
    '''
    Add a given page (could also be an index) to the fileinfo index.
    If the page already exists, then the existing fileinfo
    is updated with the new information.

    Called by the page builder routines.

    :param page:
        The page object to add to the fileinfo index.
    :param template_mapping:
        The template mapping to use for creating the page's fileinfo(s).
    :param file_path:
        The file path to use for the fileinfo.
    :param url:
        The URL to associate with the fileinfo.
    :param sitewide_file_path:
        The sitewide file path to use for the fileinfo.
    :param mapping_sort:
        Sort order for the mapping, if used.
    '''
    try:
        existing_fileinfo = FileInfo.get(
            FileInfo.sitewide_file_path == sitewide_file_path,
            FileInfo.template_mapping == template_mapping
            )

    except FileInfo.DoesNotExist:

        try:

            new_fileinfo = FileInfo.create(page=page,
                template_mapping=template_mapping,
                file_path=file_path,
                sitewide_file_path=sitewide_file_path,
                url=url,
                mapping_sort=mapping_sort)

            fileinfo = new_fileinfo

        except IntegrityError:

            from core.error import FileInfoCollision
            collision = FileInfo.get(
                FileInfo.sitewide_file_path == sitewide_file_path)
            raise FileInfoCollision('''
Template mapping #{}, {}, for template #{},
yields a path that already exists in the system: {}
This appears to be a collision with mapping {} in template {}'''.format(
                template_mapping.id,
                template_mapping.path_string,
                template_mapping.template.id,
                sitewide_file_path,
                collision.template_mapping.path_string,
                collision.template_mapping.template.for_log))


    else:

        existing_fileinfo.file_path = file_path
        existing_fileinfo.sitewide_file_path = sitewide_file_path
        existing_fileinfo.url = url
        existing_fileinfo.modified_date = datetime.datetime.utcnow()
        existing_fileinfo.mapping_sort = mapping_sort
        existing_fileinfo.save()

        fileinfo = existing_fileinfo

    return fileinfo

def delete_fileinfo_files(fileinfos):
    '''
    Iterates through the fileinfos (e.g.,for a given page)
    and deletes the physical files from disk.
    :param page:
        The page object to remove from the fileinfo index and on disk.
    '''
    deleted_files = []
    for n in fileinfos:
        try:
            if os.path.isfile(n.sitewide_file_path):
                os.remove(n.sitewide_file_path)
                _.append(n.sitewide_file_path)
        except Exception as e:
            raise e

    # return ' '.join(_)
    return deleted_files

def delete_page_fileinfo(page):
    '''
    Deletes the fileinfo entry associated with a specific page.
    This does not perform any security checks.
    This also does not delete anything from the filesystem.
    :param page:
        The page object remove from the fileinfo index.
    '''

    fileinfo_to_delete = FileInfo.delete().where(FileInfo.page == page)
    return fileinfo_to_delete.execute()

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

    unpublish_page(page, no_save=True)
    # TODO: Move this into page.delete_instance, override by way of BaseModel
    # page.kv_del()
    delete_page_fileinfo(page)
    page.delete_instance(recursive=True)

    delete_orphaned_tags(page.blog)


def unpublish_page(page, no_save=False):
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
    if not no_save:
        page.save(page.user)

    queue_page_actions((page.next_page, page.previous_page,), no_neighbors=True)
    queue_index_actions(page.blog)

    delete_fileinfo_files(page.fileinfos)



def generate_page_text(f, tags):
    '''
    Generates the text for a given page based on its fileinfo
    and a given tagset.

    :param f:
        The fileinfo object to use.
    :param tags:
        The tagset to use.
    '''

    tp = f.template_mapping.template

    try:
        tpx = template_cache[tp.id]
    except KeyError:
        try:
            pre_tags = blog_tag_cache[tp.blog.id]
        except KeyError:
            pre_tags = template_tags(blog=tp.blog)
            blog_tag_cache[tp.blog.id] = pre_tags

        tpx = MetalTemplate(source=tp.body,
            tags=pre_tags.__dict__)
        template_cache[f.template_mapping.id] = tpx

    try:
        return tpx.render(**tags.__dict__)

    except BaseException:
        import traceback, sys
        tb = sys.exc_info()[2]
        line_number = traceback.extract_tb(tb)[-1][1] - 1

        raise PageTemplateError("Error in template '{}': {} ({}) at line {}".format(
            tp.for_log,
            sys.exc_info()[0],
            sys.exc_info()[1],
            line_number
            ))




def _build_file(f, blog):
    '''
    Builds a single file based on a fileinfo entry f for a given blog.
    Returns details about the built file.

    This does _not_ perform any checking for the page's publication status,
    nor does it perform any other higher-level security.

    This should be the action that is pushed to the queue, and consolidated
    based on the generated filename. (The consolidation should be part of the queue push function)

    :param f:
        The fileinfo object to use.
    :param blog:
        The blog object to use as the context for the fileinfo.
    '''

    report = []
    begin = time.clock()
    page_text, pathname = generate_file(f, blog)
    file = time.clock()

    report.append("Output: " + pathname)
    encoded_page = page_text.encode('utf8')

    split_path = f.file_path.rsplit('/', 1)

    if len(split_path) > 1:
        path_to_check = blog.path + "/" + split_path[0]
    else:
        path_to_check = blog.path

    if os.path.isdir(path_to_check) is False:
        os.makedirs(path_to_check)

    with open(pathname, "wb") as output_file:
        output_file.write(encoded_page)

    logger.info("File '{}' built ({} bytes ({:.4f} secs)).".format(
        f.file_path,
        len(encoded_page),
        file - begin))

    return report


def generate_archive_context_from_page(context_list, original_pageset, original_page):
    return generate_archive_context(context_list, original_pageset, page=original_page)

def generate_archive_context_from_fileinfo(context_list, original_pageset, fileinfo):
    return generate_archive_context(context_list, original_pageset, fileinfo=fileinfo)

def generate_archive_context(context_list, original_pageset, **ka):
    """
    Creates the template_tags object for a given archive context,
    based on the context list string ("CYM", etc.), the original pageset
    (e.g., a blog), and the page (or fileinfo), passed as keyword arguments,
    being used to derive the archive context.

    :param context_list:
        The context list string, such as "CYM" for Category/Year/Month.
    :param original_pageset:
        The pageset used to generate the context. This is typically a blog.
    :param page:
    :param fileinfo:
        Either a page or fileinfo to generate a context for must be provided,
        as a keyword argument.
    """
    # TODO: make passing of page/fileinfo actual optional positionals?

    original_page, fileinfo = None, None

    try:
        original_page = ka['page']
    except BaseException:
        try:
            fileinfo = ka['fileinfo']
        except BaseException:
            raise BaseException("A page or a fileinfo object must be provided.", Exception)

    tag_context = original_pageset

    date_counter = {
        "year":None,
        "month":None,
        "day":None
        }

    for m in context_list:
        tag_context, date_counter = archive_functions[m]["context"](
            fileinfo, original_page, tag_context, date_counter)

    return tag_context


def category_context(fileinfo, original_page, tag_context, date_counter):

    if fileinfo is None:
        category_context = PageCategory.select(PageCategory.category).where(
            PageCategory.page == original_page)
    else:
        category_context = PageCategory.select(PageCategory.category).where(
            PageCategory.category == Category.select().where(Category.id == fileinfo.category).get())

    page_constraint = PageCategory.select(PageCategory.page).where(PageCategory.category << category_context)
    tag_context_next = tag_context.select().where(Page.id << page_constraint)
    return tag_context_next, date_counter

def year_context(fileinfo, original_page, tag_context, date_counter):

    if fileinfo is None:
        year_context = [original_page.publication_date_tz.year]
    else:
        year_context = [fileinfo.year]

    tag_context_next = tag_context.select().where(
        Page.publication_date.year << year_context)

    date_counter["year"] = True

    return tag_context_next, date_counter

def month_context(fileinfo, original_page, tag_context, date_counter):

    if date_counter["year"] is False:
        raise ArchiveMappingFormatException("An archive mapping was encountered that had a month value before a year value.", Exception)

    if fileinfo is None:
        month_context = [original_page.publication_date_tz.month]
    else:
        month_context = [fileinfo.month]

    tag_context_next = tag_context.select().where(
        Page.publication_date.month << month_context)

    date_counter["month"] = True

    return tag_context_next, date_counter

def author_context(fileinfo, original_page, tag_context, date_counter):

    if fileinfo is None:
        author_context = [original_page.author]
    else:
        author_context = [fileinfo.author]

    author_limiter = User.select().where(User.id == author_context)

    tag_context_next = tag_context.select().where(Page.user << author_limiter)

    return tag_context_next, date_counter

def page_tag_context(fileinfo, original_page, tag_context, date_counter):

    if fileinfo is None:
        page_tag_context = [original_page.context.tag]
    else:
        page_tag_context = [fileinfo.tags]

    tag_list = TagAssociation.select(TagAssociation.page).where(
        TagAssociation.tag == page_tag_context)

    tag_context_next = tag_context.select().where(
            Page.id << tag_list
        )

    # TypeError: unsupported operand type(s) for <<: 'BaseModel' and 'SelectQuery'

    return tag_context_next, date_counter

archive_functions = {
    "C":{
        "mapping":lambda x:x.primary_category.id,
        "context":category_context,
        'format':lambda x:'{}'.format(x)
        },
    "Y":{
        "mapping":lambda x:x.publication_date_tz.year,
        "context":year_context,
        'format':lambda x:'{}'.format(x)
        },
    "M":{
        "mapping":lambda x:x.publication_date_tz.month,
        "context":month_context,
        'format':lambda x:'{:02d}'.format(x)
        },
    "A":{
        "mapping":lambda x:x.user.id,
        "context":author_context,
        'format':lambda x:'{}'.format(x)
        },

    "T":{
        "mapping":lambda x:x.context.tag.id,
        "context":page_tag_context,
        'format':lambda x:'{}'.format(x)
        }
    }


import re

mapping_tags = (
    # Replacing these to allow proper computation of a Python expression
    # for template mappings
    (re.compile('\$i'), 'blog.index_file'),
    (re.compile('\$s'), 'blog.ssi_path'),
    (re.compile('\$f'), 'page.filename'),
)

def replace_mapping_tags(string):

    for n in mapping_tags:
        string = re.sub(n[0], n[1], string)

    # temporary shim

    # if string[:1] != "'":
        # string = "'" + string + "'"

    return string

def build_pages_fileinfos(pages):
    '''
    Creates fileinfo entries for the template mappings associated with
    an iterable list of Page objects.
    :param pages:
        List of page objects to build fileinfos for.
    '''

    for n, page in enumerate(pages):

        template_mappings = page.template_mappings

        if template_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for this page.')

        tags = template_tags(page=page)

        for t in template_mappings:

            path_string = replace_mapping_tags(t.path_string)
            path_string = generate_date_mapping(page.publication_date_tz.date(), tags, path_string)

            # for tag archives, we need to return a list from the date mapping
            # in the event that we have a tag present that's an iterable like the tag list
            # e.g., for /%t/%Y, for a given page that has five tags
            # we return five values, one for each tag, along with the year

            if path_string == '' or path_string is None:
                continue

            # TODO: eventually, this will be None, not ''

            master_path_string = path_string
            add_page_fileinfo(page, t, master_path_string,
                page.blog.url + "/" + master_path_string,
                page.blog.path + '/' + master_path_string,
                str(page.publication_date_tz))


    try:
        return n + 1
    except Exception:
        return 0

def build_archives_fileinfos_by_mappings(template, early_exit=False):
    counter = 0
    mapping_list = {}

    for page in template.blog.published_pages:
        tags = template_tags(page=page)
        if page.archive_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for the archives for this page.')

        for mapping in template.mappings:
            paths_list = eval_paths(mapping.path_string, tags.__dict__)

            if type(paths_list) in (list,):
                paths = []
                for n in paths_list:
                    if n is None:
                        continue
                    p = page.proxy(n[0])
                    paths.append((p, n[1]))
            else:
                paths = (
                    (page, paths_list)
                    ,)

            for page, path in paths:
                path_string = generate_date_mapping(page.publication_date_tz,
                    tags, path, do_eval=False)

                if path_string == '' or path_string is None:
                    continue
                if path_string in mapping_list:
                    continue

                mapping_list[path_string] = (
                    (None, mapping, path_string,
                    page.blog.url + "/" + path_string,
                    page.blog.path + '/' + path_string,)
                    ,
                    (page),
                    )

        if early_exit and len(mapping_list) > 0:
            break

    for counter, n in enumerate(mapping_list):
        # TODO: we should bail if there is already a fileinfo for this page?
        new_fileinfo = add_page_fileinfo(*mapping_list[n][0])
        archive_context = []
        m = mapping_list[n][0][1]

        for r in m.archive_xref:
            archive_context.append(
                archive_functions[r]["format"](
                    archive_functions[r]["mapping"](mapping_list[n][1])
                    )
                )

        for t, r in zip(archive_context, m.archive_xref):
            new_fileinfo_context = FileInfoContext.get_or_create(
                fileinfo=new_fileinfo,
                object=r,
                ref=t
                )

        new_fileinfo.mapping_sort = archive_context
        new_fileinfo.save()

    try:
        return counter + 1
    except Exception:
        return 0

def build_archives_fileinfos(pages):
    '''
    Takes a page (maybe a collection of same) and produces fileinfos
    for the date-based archive entries for each
    :param pages:
        List of pages to produce fileinfos for date-based archive entries for.
    '''

    counter = 0
    mapping_list = {}

    # FIXME:
    # get all the pages, collect all the archive mappings,
    # coalesce them, then work on the archive mappings as the outer loop

    for page in pages:
        tags = template_tags(page=page)
        if page.archive_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for the archives for this page.')
        for m in page.archive_mappings:
            paths_list = eval_paths(m.path_string, tags.__dict__)
            if type(paths_list) in (list,):
                paths = []
                for n in paths_list:
                    if n is None:
                        continue
                    p = page.proxy(n[0])
                    paths.append((p, n[1]))
            else:
                paths = (
                    (page, paths_list)
                    ,)

            for page, path in paths:
                path_string = generate_date_mapping(page.publication_date_tz,
                    tags, path, do_eval=False)

                if path_string == '' or path_string is None:
                    continue
                if path_string in mapping_list:
                    continue

                mapping_list[path_string] = (
                    (None, m, path_string,
                    page.blog.url + "/" + path_string,
                    page.blog.path + '/' + path_string,)
                    ,
                    (page),
                    )

    for counter, n in enumerate(mapping_list):
        # TODO: we should bail if there is already a fileinfo for this page?
        new_fileinfo = add_page_fileinfo(*mapping_list[n][0])
        archive_context = []
        m = mapping_list[n][0][1]

        for r in m.archive_xref:
            archive_context.append(
                archive_functions[r]["format"](
                    archive_functions[r]["mapping"](mapping_list[n][1])
                    )
                )

        for t, r in zip(archive_context, m.archive_xref):
            new_fileinfo_context = FileInfoContext.get_or_create(
                fileinfo=new_fileinfo,
                object=r,
                ref=t
                )

        new_fileinfo.mapping_sort = archive_context
        new_fileinfo.save()

    try:
        return counter + 1
    except Exception:
        return 0

def build_indexes_fileinfos(templates):

    '''
    Rebuilds a fileinfo entry for a given main index.

    This will need to be run every time we create a new index type,
    or change a mapping. (Most of these should have a 1:1 mapping)

    A control message should not be needed, since these are 1:1

    This will port the code currently found in build_blog_fileinfo, much as the above function did.

    :param templates:
        A list of templates, typically for main indexes, to rebuild fileinfo entries for.

    '''
    for n, template in enumerate(templates):

        index_mappings = TemplateMapping.select().where(
            TemplateMapping.template == template)

        blog = index_mappings[0].template.blog


        tags = template_tags(blog_id=blog.id)

        for i in index_mappings:
            path_string = replace_mapping_tags(i.path_string)
            path_string = eval(path_string, tags.__dict__)

            if path_string == '' or path_string is None:
                continue

            # why are we doing this twice?
            # path_string = replace_mapping_tags(path_string)

            # raise Exception(path_string)

            master_path_string = path_string
            add_page_fileinfo(None, i, master_path_string,
                 blog.url + "/" + master_path_string,
                 blog.path + '/' + master_path_string)

    try:
        return n + 1
    except Exception:
        return 0


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

    # import time

    # blog = Blog.load(blog_id)

    data = []
    data.extend(["<h3>Queuing <b>{}</b> for republishing</h3><hr>".format(
        blog.for_log)])

    begin = time.clock()

    queue_ssi_actions(blog)

    queue_page_actions(blog.published_pages.iterator(), no_neighbors=True)

    queue_index_actions(blog, include_manual=True)

    end = time.clock()

    data.append("Total processing time: {0:.2f} seconds.".format(end - begin))
    data.append("<hr/><a href='{}/blog/{}/publish'>Click here to activate the publishing queue.</a>".format(
        BASE_URL,
        blog.id))
    return data

def process_queue_publish(queue_control, blog):
    '''
    Processes the publishing queue for a given blog.
    Takes in a queue_control entry, and returns an integer of the number of
    jobs remaining in the queue for that blog.
    Typically invoked by the process_queue function.

    :param queue_control:
        The queue_control entry, from the queue, to use for this publishing queue run.
    :param blog:
        The blog object that is in context for this job.
    '''

    template_cache = {}
    blog_tag_cache = {}

    queue_control.is_running = True
    queue_control.save()

    queue = Queue.select().order_by(Queue.priority.desc(),
        Queue.date_touched.desc()).where(Queue.blog == blog,
        Queue.is_control == False).limit(MAX_BATCH_OPS).naive()

    queue_length = queue.count()

    # import time

    start_queue = time.clock()

    if queue_length > 0:
        logger.info("Queue job #{} @ {} (blog #{}, {} items) started.".format(
            queue_control.id,
            date_format(queue_control.date_touched),
            queue_control.blog.id,
            queue_length))

    removed_jobs = []

    for q in queue.iterator():
        try:
            job_type.action[q.job_type](q)
        except Exception as e:
            raise e
        else:
            removed_jobs.append(q.id)

    remove_from_queue(removed_jobs)

    queue_control = Queue.get(Queue.blog == blog,
        Queue.is_control == True)

    queue_control.data_integer -= queue_length

    end_queue = time.clock()

    total_time = end_queue - start_queue
    if queue_control.data_integer <= 0:
        queue_control.delete_instance()
        logger.info("Queue job #{} @ {} (blog #{}) finished ({:.4f} secs).".format(
            queue_control.id,
            date_format(queue_control.date_touched),
            queue_control.blog.id,
            total_time))

    else:
        queue_control.is_running = False
        queue_control.save()
        logger.info("Queue job #{} @ {} (blog #{}) continuing with {} items left ({:.4f} secs).".format(
            queue_control.id,
            date_format(queue_control.date_touched),
            queue_control.blog.id,
            queue_length,
            total_time))

    return queue_control.data_integer

def process_queue_insert(queue_control, blog):

    # Queue for building fileinfo data
    # e.g., when a blog is rebuilt

    # We don't have a front end for this yet?
    # Why .delete_instance()? Shouldn't we just set to 0?

    # also, why isn't this running inside a transaction?

    queue_control.is_running = True
    queue_control.save()

    result = 0

    if queue_control.data_string == 'page_fileinfos':
        page_list = blog.pages.order_by(Page.id.desc())
        index = page_list.count() - queue_control.data_integer
        n = 0
        while n < MAX_BATCH_OPS and index < page_list.count():
            build_pages_fileinfos((page_list[index],))
            build_archives_fileinfos((page_list[index],))
            index += 1
            n += 1

        if index >= page_list.count():
            queue_control.delete_instance()
        else:
            queue_control.data_integer -= n

        result = page_list.count() - index

    if queue_control.data_string == 'index_fileinfos':
        index_list = blog.templates(template_type.index)
        index = index_list.count() - queue_control.data_integer
        n = 0
        while n < MAX_BATCH_OPS and index < index_list.count():
            build_indexes_fileinfos((index_list[index],))
            index += 1
            n += 1

        if index >= index_list.count():
            queue_control.delete_instance()
        else:
            queue_control.data_integer -= n

        result = index_list.count() - index

    if queue_control.data_string == 'ssi_fileinfos':
        pass
        # TODO: to be added

    queue_control.is_running = False
    queue_control.save()

    return result

def process_queue(blog):
    '''
    Processes the jobs currently in the queue for the selected blog.
    '''

    with db.atomic():

        q_c = publishing_lock(blog, True)

        if q_c is None:
            return 0

        queue_control = q_c[0]

        if queue_control.job_type == job_type.control:
            process_queue_publish(queue_control, blog)
        elif queue_control.job_type == job_type.insert:
            process_queue_insert(queue_control, blog)

    return Queue.job_counts(blog=blog)

def build_mapping_xrefs(mapping_list):

    import re
    iterable_tags = (
        (re.compile('%Y'), 'Y'),
        (re.compile('%m'), 'M'),
        (re.compile('%d'), 'D'),
        (re.compile('page\.categories.?'), 'C'),
        (re.compile('page\.user.?'), 'A'),
        (re.compile('page\.author.?'), 'A'),
        (re.compile('page\.tags.?'), 'T')
        # (re.compile('page\.primary_category.?'), 'P'),
        )

    map_types = {}

    for mapping in mapping_list:
        purge_fileinfos(mapping.fileinfos)

        match_pos = []

        # TODO: make sure we don't append the same thing twice

        for tag, func in iterable_tags:
            match = tag.search(mapping.path_string)
            if match is not None:
                match_pos.append((func, match.start()))

        sorted_match_list = sorted(match_pos, key=lambda row: row[1])
        context_string = "".join(n for n, m in sorted_match_list)
        mapping.archive_xref = context_string
        mapping.save()

        map_types[mapping.template.template_type] = ""

    # TODO: make all these actions queueable

    if 'Page' in map_types:
        # build_pages_fileinfos(mapping.template.blog.pages)
        pass
    if 'Archive' in map_types:
        # TODO: eventually build only the mappings for the affected template, not all of them
        pass
        # build_archives_fileinfos(mapping.template.blog.published_pages)
    if 'Index' in map_types:
        # TODO: eventually build only the mappings for the affected template, not all of them
        build_indexes_fileinfos(mapping.template.blog.index_templates)
    if 'Include' in map_types:
        # TODO: eventually build only the mappings for the affected template, not all of them
        build_indexes_fileinfos(mapping.template.blog.ssi_templates)

def purge_fileinfos(fileinfos):
    '''
    Takes a collection of fileinfos in the form of a model
    and removes them from the fileinfo list.
    Returns how many entries were purged.
    No security checks are performed.
    '''
    context_purge = FileInfoContext.delete().where(FileInfoContext.fileinfo << fileinfos)
    n = context_purge.execute()
    purge = FileInfo.delete().where(FileInfo.id << fileinfos)
    m = purge.execute()
    return m, n


def purge_blog(blog):
    '''
    Deletes all fileinfos from a given blog and recreates them.
    This function may also eventually be expanded to delete all the files
    associated with a given blog (except for assets)
    No security checks are performed.

    Eventually we will make each of these purge and append actions
    into queueable behaviors, so that these operations don't time out.

    '''

    # import time

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

def register_media(filename, path, user, **ka):

    media = Media(
        filename=filename,
        path=path,
        type=media_filetypes.types[os.path.splitext(filename)[1][1:]],
        user=user,
        friendly_name=ka.get('friendly_name', filename)
        )

    media.save()

    if 'page' in ka:
        page = ka['page']
        media.associate(page)
        media.blog = page.blog
        media.site = page.blog.site
        media.url = page.blog.url + "/" + page.blog.media_path + "/" + media.filename
        media.save()

    return media

def start_queue(blog=None, queue_length=None, jobtype=job_type.control):

    if jobtype == job_type.control:
        if blog is None:
            raise Exception("You must specify a blog when starting a queue process.")
        if queue_length is None:
            queue_length = Queue.job_counts(blog=blog)
    else:
        pass
        # handle job_type.insert queue length here

    push_to_queue(blog=blog,
        site=blog.site,
        job_type=jobtype,

        # TODO: eventually this will include insert jobs as well
        # Make sure the queue is locked properly when we do that
        # and when we do the insert, perhaps we should get the total number
        # of prospective jobs from a model object.
        # for instance, if we want to push all the insert jobs
        # for a given template, we can get that directly from the template
        # likewise, for a whole blog (all template objects)
        # likewise, for other classes of objects (e.g., all the templates from a page)
        # easiest to start with just individual templates or whole blogs,
        # since those are easy to calculate and coalesce

        is_control=True,
        data_integer=queue_length
        )

    return queue_length
