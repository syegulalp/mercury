import os

from core.utils import generate_date_mapping, date_format
from core.error import NoArchiveForFileInfo
from core.log import logger
from core.libs.peewee import OperationalError

from core.models import (Page, Template, TemplateMapping, template_type,
    FileInfo, template_tags, Struct, publishing_mode, Queue)

from .fileinfo import (generate_page_tags, delete_fileinfo_files, build_pages_fileinfos,
    build_archives_fileinfos, build_indexes_fileinfos, eval_paths)
from . import generate_page_text

from settings import MAX_BATCH_OPS, LOOP_TIMEOUT
import time

from threading import Thread
t = Thread()
t.daemon = True
from queue import Queue as Q
write_queue = Q()

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
        if page is None:
            continue

        try:

            blog, site = page.blog, page.blog.site

            for f in page.fileinfos:
                if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:
                    Queue.push(job_type=job_type.page,
                        blog=blog,
                        site=site,
                        priority=8,
                        data_integer=f.id)

            if no_archive is False:
                queue_page_archive_actions(page)

            if no_neighbors is False:

                next_page = page.next_page
                previous_page = page.previous_page

                if next_page is not None:

                    for f in next_page.fileinfos:

                        if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:

                            Queue.push(job_type=job_type.page,
                                blog=blog,
                                site=site,
                                priority=8,
                                data_integer=f.id)

                            queue_page_archive_actions(next_page)

                if previous_page is not None:

                    for f in previous_page.fileinfos:

                        if f.template_mapping.template.publishing_mode != publishing_mode.do_not_publish:

                            Queue.push(job_type=job_type.page,
                                blog=blog,
                                site=site,
                                priority=8,
                                data_integer=f.id)

                            queue_page_archive_actions(previous_page)

        except OperationalError as e:
            raise e
        except Exception as e:
            from core.error import QueueAddError
            raise QueueAddError('Page {} could not be queued: '.format(
                page.for_log,
                e))


def build_page(queue_entry, async_write=False):
    try:
        fileinfo = FileInfo.get(FileInfo.id == queue_entry.data_integer)
        blog = queue_entry.blog
        page_tags = generate_page_tags(fileinfo, blog)
        file_page_text = generate_page_text(fileinfo, page_tags)
        if async_write:
            if not t.is_alive:
                t.target = write_file_queue
                t.args = (write_queue,)
                t.start()
            write_queue.put_nowait((file_page_text, blog.path, fileinfo.file_path))
        else:
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


def write_file_queue(q):
    while 1:
        a, b, c = q.get()
        write_file(a, b, c)
        q.task_done()


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
    # from . import invalidate_cache
    # invalidate_cache()

    queue_control.lock()

    queue_original = Queue.select().order_by(Queue.priority.desc(),
        Queue.date_touched.desc()).where(Queue.blog == blog,
        Queue.is_control == False)

    queue = queue_original.limit(MAX_BATCH_OPS).naive()

    queue_original_length = queue_original.count()
    queue_length = queue.count()

    start_queue = time.clock()

    if queue_length > 0:
        logger.info("Queue job #{} @ {} (blog #{}, {} items) started.".format(
            queue_control.id,
            date_format(queue_control.date_touched),
            queue_control.blog.id,
            queue_original_length))

    removed_jobs = []

    start = time.clock()

    for q in queue:
        job_type.action[q.job_type](q)
        removed_jobs.append(q.id)

        if (time.clock() - start) > LOOP_TIMEOUT:
            break

    Queue.remove(removed_jobs)

    # we don't need to have an entirely new job!
    # we should recycle the existing one, yes?

    new_queue_control = Queue.control_job(blog)

    # new_queue_control = Queue.get(Queue.blog == blog,
        # Queue.is_control == True)

    queue_original_length -= len(removed_jobs)
    new_queue_control.data_integer = queue_original_length

    end_queue = time.clock()

    total_time = end_queue - start_queue
    if new_queue_control.data_integer <= 0:
        new_queue_control.delete_instance()
        logger.info("Queue job #{} @ {} (blog #{}) finished ({:.4f} secs).".format(
            new_queue_control.id,
            date_format(new_queue_control.date_touched),
            new_queue_control.blog.id,
            total_time))

    else:
        # new_queue_control.is_running = False
        # new_queue_control.save()
        new_queue_control.unlock()
        logger.info("Queue job #{} @ {} (blog #{}) processed {} items ({:.4f} secs, {} remaining).".format(
            new_queue_control.id,
            date_format(new_queue_control.date_touched),
            new_queue_control.blog.id,
            len(removed_jobs),
            total_time,
            queue_original_length,
            ))

    return new_queue_control.data_integer


def process_queue_insert(queue_control, blog):

    # Queue for building fileinfo data
    # e.g., when a blog is rebuilt

    # We don't have a front end for this yet?
    # Why .delete_instance()? Shouldn't we just set to 0?

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

    queue_control = Queue.acquire(blog, True)

    if queue_control is None:
        return 0

    if queue_control.job_type == job_type.control:
        process_queue_publish(queue_control, blog)
    elif queue_control.job_type == job_type.insert:
        process_queue_insert(queue_control, blog)

    return Queue.job_counts(blog=blog)


def queue_page_archive_actions(page):
    '''
    Pushes to the publishing queue all the page archives for a given page object.

    :param page:
        The page object whose archives will be pushed to the publishing queue.
    '''

    #===========================================================================
    # NOTE: I tried to speed this up by checking the list of fileinfos
    # related to mappings for the page (if any), and then pushing those
    # if they exist, but I haven't seen evidence it does anything tangible
    # for performance.
    # I need to double-check that old mappings are in fact invalidated
    # when they are changed.
    #===========================================================================

    archive_templates = page.blog.archive_templates
    tags = template_tags(page=page)

    for n in archive_templates:
        try:
            if n.publishing_mode != publishing_mode.do_not_publish:
                fileinfo_mappings = FileInfo.select().where(FileInfo.page == page,
                                                 FileInfo.template_mapping << n.mappings)
                # page.archive_mappings)
                if fileinfo_mappings.count() > 0:
                    for fileinfo_mapping in fileinfo_mappings:
                        Queue.push(job_type=job_type.archive,
                                      blog=page.blog,
                                      site=page.blog.site,
                                      priority=7,
                                      data_integer=fileinfo_mapping.id)

                else:

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

                            try:
                                fileinfo_mapping = FileInfo.get(FileInfo.sitewide_file_path == file_path)
                            except FileInfo.DoesNotExist:
                                if build_archives_fileinfos((page,)) == 0:
                                    from core.error import QueueAddError
                                    raise QueueAddError(
                                        'No archive fileinfos could be built for page {} with template {}'.format(
                                        page.for_log,
                                        n.template.for_log))

                            Queue.push(job_type=job_type.archive,
                                      blog=page.blog,
                                      site=page.blog.site,
                                      priority=7,
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
            Queue.push(
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
        Queue.push(job_type=job_type.index,
            priority=1,
            blog=blog,
            site=blog.site,
            data_integer=f.id)

