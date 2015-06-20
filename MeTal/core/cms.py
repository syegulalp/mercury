import os, datetime

from core.utils import (create_basename, Status, tpl, generate_date_mapping, date_format)
from core.error import (ArchiveMappingFormatException, PageNotChanged, EmptyQueueError,
    QueueInProgressException, PageTemplateError)
from core.log import logger

from libs.bottle import request
from libs.peewee import DeleteQuery
import json

from models import (db, Page, Template, TemplateMapping, TagAssociations, Tags, template_type,
    Categories, PageCategories, FileInfo, Queue, template_tags, get_blog, User,
    FileInfoContext, Media, MediaAssociation, Struct, page_status)

from settings import MAX_BATCH_OPS

save_actions = Struct()  

save_actions.SAVE_TO_DRAFT = 1 
save_actions.UPDATE_LIVE_PAGE = 2
save_actions.EXIT_EDITOR = 4
save_actions.UNPUBLISH_PAGE = 8
save_actions.DELETE_PAGE = 16

job_type = Struct()
job_type.page = "Page"
job_type.index = "Index"
job_type.control = "Control"

job_type.description = {
    job_type.page: 'Page entry',
    job_type.index: 'Index entry',
    job_type.control: 'Control job'
    }

job_type.action = {
    job_type.page: lambda x:build_page(x),  # build_page
    job_type.index: lambda x:build_page(x)  # build_index
    }

def build_page(q):
    '''
    Builds the file for a single blog page, q, based on its fileinfo data. 
    '''
    fileinfo = FileInfo.get(FileInfo.id == q.data_integer)
    try:
        build_file(fileinfo, q.blog)
    except BaseException:
        raise

def push_to_queue(**ka):
    '''
    Inserts a single job item into the work queue.
    
    :param job_type:
        A string representing the type of job to be inserted.
        'Page','Index', eventually 'Fileinfo'
        
    :param data_integer:
        Any integer data passed along with the job. For a job control item, this
        is the number of items remaining for that particular job.
    
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
    
    queue_job.job_type = ka['job_type']
    
    if 'data_integer' in ka:
        queue_job.data_integer = int(ka['data_integer'])
    
    if 'blog' in ka:
        queue_job.blog = ka['blog'].id
        queue_job.site = ka['blog'].site.id 
    
    if 'site' in ka:
        queue_job.site = ka['site'].id
        
    if 'priority' in ka:
        
        queue_job.priority = ka['priority']
        
    if 'is_control' in ka:
        
        queue_job.is_control = True
    
    if queue_job.job_type == job_type.page:
        
        queue_job.data_string = "Page: " + FileInfo.get(FileInfo.id == queue_job.data_integer).file_path
        
    if queue_job.job_type == job_type.index:
        
        queue_job.data_string = "Index: " + FileInfo.get(FileInfo.id == queue_job.data_integer).file_path
        
    queue_job.date_touched = datetime.datetime.now()    
    queue_job.save()

def remove_from_queue(queue_id):
    '''
    Removes a specific job ID from the queue.

    :param queue_id:
        The ID number of the job queue item to remove.

    '''    
    
    queue_delete = Queue.get(Queue.id == queue_id)
    return queue_delete.delete_instance()

def queue_page_actions(page, no_neighbors=False, no_archive=False):
    '''
    Pushes a page along with all its related items into the queue for publication.
    This includes any archive indices associated with the page, and the page's next and
    previous entries in its respective categories. Note that this will only queue
    items that are actually published.

    :param page:
        The page object whose actions are to be queued.
    :param no_neighbors:
        Set to True to suppress generation of next/previous posts. Useful if you've loaded
        all the posts for a blog into a queue.
    :param no_archove:
        Set to True to suppress generation of archive pages associated with this page. Also
        useful for mass-queued actions.
    '''

    fileinfos = FileInfo.select().where(FileInfo.page == page)
    
    blog = page.blog
    site = page.blog.site
    
    for f in fileinfos:
        push_to_queue(job_type=job_type.page,
            blog=blog,
            site=site,
            data_integer=f.id)

    if no_archive is False:
        queue_page_archive_actions(page)    
    
    if no_neighbors is False:
            
        next_page = page.next_page 
        previous_page = page.previous_page
        
        # Next and previous across categories should be done through this
        # mechanism somehow
         
        if next_page is not None:
            
            
            fileinfos_next = FileInfo.select().where(FileInfo.page == next_page)
            
            for f in fileinfos_next:
        
                push_to_queue(job_type=job_type.page,
                    blog=blog,
                    site=site,
                    data_integer=f.id)
                
            queue_page_archive_actions(next_page)
            
        if previous_page is not None:
        
            fileinfos_previous = FileInfo.select().where(FileInfo.page == previous_page)
    
            for f in fileinfos_previous:
            
                push_to_queue(job_type=job_type.page,
                    blog=blog,
                    site=site,
                    data_integer=f.id)    
    
            queue_page_archive_actions(previous_page)

def queue_page_archive_actions(page):
    '''
    Pushes to the publishing queue all the page archives for a given page object.
    '''
    
    archive_templates = page.blog.archive_templates
    tags = template_tags(page_id=page.id)
    
    for n in archive_templates:
        for m in n.mappings:
            
            file_path = (page.blog.path + '/' + 
                         generate_date_mapping(page.publication_date.date(),
                                               tags,
                                               m.path_string))

            fileinfo_mapping = FileInfo.get(FileInfo.sitewide_file_path == file_path)
            
            push_to_queue(job_type=job_type.page,
                          blog=page.blog,
                          site=page.blog.site,
                          data_integer=fileinfo_mapping.id)  
    
def queue_index_actions(blog):
    '''
    Pushes to the publishing queue all the index pages for a given blog
    that are marked for Immediate publishing.
    '''
    
    try:
        templates = Template.select().where(Template.blog == blog,
            Template.template_type == template_type.index,
            Template.publishing_mode == 'Immediate')
        
        if templates.count() == 0:
            raise Template.DoesNotExist
        
    except Template.DoesNotExist:
        raise Template.DoesNotExist("No index templates exist for blog {}.".format(
            blog.for_log)) 
    
    else:
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
        
        page.publication_date = datetime.datetime.now()
        page.created_date = datetime.datetime.now()

    else:

        original_page_status = page.status
        original_page_basename = page.basename
        
        page.modified_date = datetime.datetime.now()
        
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
    page.publication_date = datetime.datetime.strptime(request.forms.get('publication_date'), '%Y-%m-%d %H:%M:%S')
    page.tag_text = request.forms.getunicode('page_tag_text')
    page.excerpt = request.forms.getunicode('page_excerpt')
    
    change_note = request.forms.getunicode('change_note') 
    
    # Save to draft only
    # Save and publish
    # Save and exit
    # Republish and exit
    # Unpublish (and exit)
    # Delete (and unpublish) (and exit)
    
    msg = ""

    # UNPUBLISH
    if (
        (save_action & save_actions.UNPUBLISH_PAGE and page.status == page_status.published) or  # unpublished a published page
        (original_page_status == page_status.published and page.status == page_status.unpublished) or  # set a published page to draft 
        (save_action & save_actions.DELETE_PAGE)  # delete a page, regardless of status
        ): 
        
        pass
        

    # DELETE; IMPLIES UNPUBLISH
    if (save_action & save_actions.DELETE_PAGE):
        
        pass
        
    # UNPUBLISHED TO PUBLISHED
    if original_page_status == page_status.unpublished and (save_action & save_actions.UPDATE_LIVE_PAGE):
        
        page.status = page_status.published
    
    # SAVE DRAFT    
    if (save_action & save_actions.SAVE_TO_DRAFT):
        
        backup_only = True if request.forms.getunicode('draft') == "Y" else False
        try:
            save_result = page.save(user, False, backup_only, change_note)
        except PageNotChanged:
            save_result = (None, None)
        
        if blog_new_page:
    
            default_blog_category = Categories.get(
                Categories.blog == blog.id,
                Categories.default == True)
    
            saved_page_category = PageCategories.create(
                page=page,
                category=default_blog_category,
                primary=True)
            
        msg += ("Page <b>{}</b> saved.")
        
    # SET TAGS
    
    # when to do this?
    # what happens when we delete a page?
    # all tags for a page have to be deassigned.
    
    if request.forms.getunicode('tag_text') is not None:
        tag_text = json.loads(request.forms.getunicode('tag_text'))
        add_tags_to_page(tag_text, page)
        delete_orphaned_tags()
        
    
    # BUILD FILEINFO IF NO DELETE ACTION
    if not (save_action & save_actions.DELETE_PAGE):
        
        build_page_fileinfo(page)
        build_archive_fileinfo((page,))        

    # PUBLISH CHANGES        
    if (save_action & save_actions.UPDATE_LIVE_PAGE) and (page.status == page_status.published):

        queue_page_actions(page)
        queue_index_actions(page.blog)
        
        msg += (" Live page updated.")

    if (save_action & (save_actions.SAVE_TO_DRAFT + save_actions.UPDATE_LIVE_PAGE)) and (save_result[1]) is None:
        msg += (" (Page unchanged.)")
        
    tags = template_tags(page_id=page.id, user=user)

    status = Status(
        type='success',
        message=msg,
        vals=(page.title,)
        )

    tags.status = status
    
    return tags

def delete_orphaned_tags():
    '''
    Cleans up tags that no longer have any page associations.
    '''
    orphaned_tags = Tags.delete().where(
        ~Tags.id << (TagAssociations.select(TagAssociations.tag)))
    
    orphaned_tags.execute()
    
    return orphaned_tags

def add_tags_to_page (tag_text, page):
    tag_list = Tags.select().where(Tags.id << tag_text)
    
    tags_to_delete = TagAssociations.delete().where(
        TagAssociations.page == page,
        ~ TagAssociations.tag << (tag_list))
    
    tags_to_delete.execute()
    
    tags_in_page = page.tags.select(Tags.id).tuples()
    
    tags_to_add = tag_list.select().where(~Tags.id << (tags_in_page))
    
    for n in tags_to_add:
        add_tag = TagAssociations(
           tag=n,
           page=page)
        
        add_tag.save()
        
    new_tags = json.loads(request.forms.getunicode('new_tags'))
    
    for n in new_tags:
        new_tag = Tags(
            tag=n,
            blog=page.blog)
        new_tag.save()
        
        add_tag = TagAssociations(
            tag=new_tag,
            page=page)
        
        add_tag.save()
        
    return tags_to_add, tags_to_delete, new_tags

def add_page_fileinfo(page, template_mapping, file_path,
        url, sitewide_file_path):
    '''
    Add a given page (could also be an index) to the fileinfo index.
    Called by the page builder routines.
    '''
    try:
        existing_fileinfo = FileInfo.get(
            FileInfo.sitewide_file_path == sitewide_file_path,
            FileInfo.template_mapping == template_mapping
            )
        
    except FileInfo.DoesNotExist:

        new_fileinfo = FileInfo.create(page=page,
            template_mapping=template_mapping,
            file_path=file_path,
            sitewide_file_path=sitewide_file_path,
            url=url)
        
        fileinfo = new_fileinfo
        
    else:

        existing_fileinfo.file_path = file_path
        existing_fileinfo.sitewide_file_path = sitewide_file_path
        existing_fileinfo.url = url     
        
        existing_fileinfo.modified_date = datetime.datetime.now()
        existing_fileinfo.save()
        
        fileinfo = existing_fileinfo
            
    return fileinfo


def delete_page_fileinfo(page):
    '''
    Deletes the fileinfo entry associated with a specific page.
    This does not perform any security checks.
    This also does not delete anything from the filesystem.
    '''
    
    fileinfo_to_delete = FileInfo.delete().where(FileInfo.page == page)
    
    return fileinfo_to_delete.execute()


def unpublish_page(page, remove_fileinfo=False):
    '''
    Removes all the physical files associated with a given page,
    and queues any related files
    
    '''

    pass


def generate_page_text(f, tags):
    '''
    Generates the text for a given page based on its fileinfo
    and a given tagset.
    '''
    from core.template import expand_includes
    
    tp = f.template_mapping.template
    
    try:
        return tpl(expand_includes(tp),
            **tags.__dict__)
    except BaseException:
        import traceback, sys
        tb = sys.exc_info()[2]
        line_number = traceback.extract_tb(tb)[-1][1] - 1
        
        raise PageTemplateError("Error in template '{}': {} ({}) at line {}".format(
            tp.title_for_log,
            sys.exc_info()[0],
            sys.exc_info()[1],
            line_number
            ))
        
    
def build_file(f, blog):
    '''
    Builds a single file based on a fileinfo entry f for a given blog.
    Returns details about the built file.
    
    This does _not_ perform any checking for the page's publication status,
    nor does it perform any other higher-level security.
    
    This should be the action that is pushed to the queue, and consolidated
    based on the generated filename. (The conslidation should be part of the queue push function)    
    '''

    report = []
    split_path = f.file_path.rsplit('/', 1)
    path_to_check = blog.path + "/" + f.file_path.rsplit('/', 1)[0]

    if len(split_path) > 1:
        if os.path.isdir(path_to_check) is False:
            os.makedirs(path_to_check)

    if f.page is None:

        if f.xref.archive_type in [1]:
            tags = template_tags(blog_id=blog.id)
        else:
        
            archive_pages = generate_archive_context_from_fileinfo(
                f.xref.archive_xref, blog.published_pages(), f)
    
            tags = template_tags(blog_id=blog.id,
                archive=archive_pages,
                archive_context=f)
            
    else:
        tags = template_tags(page_id=f.page.id)

    page_text = generate_page_text(f, tags)
    pathname = blog.path + "/" + f.file_path
    report.append("Output: " + pathname)
    
    encoded_page = page_text.encode('utf8')
    
    with open(pathname, "wb") as output_file: 
        output_file.write(encoded_page)
    
    logger.info("File '{}' built ({} bytes).".format(
        f.file_path,
        len(encoded_page)))

    return report


def generate_archive_context_from_page(context_list, original_pageset, original_page):
    
    return generate_archive_context(context_list, original_pageset, page=original_page)

def generate_archive_context_from_fileinfo(context_list, original_pageset, fileinfo):
    
    return generate_archive_context(context_list, original_pageset, fileinfo=fileinfo)

def generate_archive_context(context_list, original_pageset, **ka):
    """
    Creates the template_tags object for a given archive context,
    based on the context list string ("CYM", etc.), the original pageset
    (e.g., a blog), and the page (or fileinfo) being used to derive the archive context.
    """
    
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
        
        tag_context, date_counter = archive_functions[m]["context"](fileinfo, original_page, tag_context, date_counter)

    return tag_context




def category_context(fileinfo, original_page, tag_context, date_counter):
    
    if fileinfo is None:
        category_context = PageCategories.select(PageCategories.category).where(
            PageCategories.page == original_page)
    else:
        category_context = PageCategories.select(PageCategories.category).where(
            PageCategories.category == Categories.select().where(Categories.id == fileinfo.category).get())
        
    page_constraint = PageCategories.select(PageCategories.page).where(PageCategories.category << category_context)
    tag_context_next = tag_context.select().where(Page.id << page_constraint)
    return tag_context_next, date_counter

def year_context(fileinfo, original_page, tag_context, date_counter):

    if fileinfo is None:
        year_context = [original_page.publication_date.year]
    else:
        year_context = [fileinfo.year]
    
    tag_context_next = tag_context.select().where(Page.publication_date.year << year_context)
    
    date_counter["year"] = True
    
    return tag_context_next, date_counter
 
def month_context(fileinfo, original_page, tag_context, date_counter):

    if date_counter["year"] is False:
        raise ArchiveMappingFormatException("An archive mapping was encountered that had a month value before a year value.", Exception)
    
    if fileinfo is None:
        month_context = [original_page.publication_date.month]
    else:
        month_context = [fileinfo.month]
    
    tag_context_next = tag_context.select().where(Page.publication_date.month << month_context)
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


archive_functions = {
    "C":{
        "mapping":lambda x:x.primary_category.id,
        "context":category_context
        },
    "Y":{
        "mapping":lambda x:x.publication_date.year,
        "context":year_context
        },
    "M":{
        "mapping":lambda x:x.publication_date.month,
        "context":month_context
        },
    "A":{
        "mapping":lambda x:x.user.id,
        "context":author_context}
    }

def build_page_fileinfo(page_id):
    '''
    Creates fileinfo entries for the template mappings associated with
    individual pages.
    '''

    page = Page.get(id=page_id)
    template_mappings = page.template_mappings
    
    if template_mappings.count() == 0:
        raise TemplateMapping.DoesNotExist('No template mappings found for this page.')
    
    tags = template_tags(page_id=page.id)

    for t in template_mappings:

        path_string = generate_date_mapping(page.publication_date.date(), tags, t.path_string)
        master_path_string = path_string + "." + page.blog.base_extension       
        add_page_fileinfo(page, t, master_path_string,
            page.blog.url + "/" + master_path_string,
            page.blog.path + '/' + master_path_string)


def build_archive_fileinfo(pages):
    '''
    Takes a page (maybe a collection of same) and produces fileinfos for the date-based archive entries for each
    '''
    
    mapping_list = {}
        
    for page in pages:
        
        tags = template_tags(page_id=page.id)
        
        if page.archive_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for the archives for this page.')
        
        for m in page.archive_mappings:
    
            path_string = generate_date_mapping(page.publication_date, tags, m.path_string)
            if path_string in mapping_list:
                continue
            
            tag_context = generate_archive_context_from_page(m.archive_xref, page.blog, page)
            mapping_list[path_string] = (None, m, path_string,
                               page.blog.url + "/" + path_string,
                               page.blog.path + '/' + path_string)            

    for n in mapping_list:
        
        fileinfo = add_page_fileinfo(*mapping_list[n])
        archive_context = []
        m = mapping_list[n][1]
        
        for n in m.archive_xref:
            archive_context.append(archive_functions[n]["mapping"](page))
                
        for t, r in zip(archive_context, m.archive_xref):
            new_fileinfo_context = FileInfoContext.get_or_create(
                fileinfo=fileinfo,
                object=r,
                ref=t)
        
    return mapping_list

def build_index_fileinfo(template_id):

    '''
    Rebuilds a fileinfo entry for a given main index.
    
    This will need to be run every time we create a new index type,
    or change a mapping. (Most of these should have a 1:1 mapping)
    
    A control message should not be needed, since these are 1:1    
    
    This will port the code currently found in build_blog_fileinfo, much as the above function did.
    
    '''
    
    report = []
    
    index_mappings = TemplateMapping.select().where(
        TemplateMapping.id == template_id)
    
    blog = index_mappings[0].template.blog

    tags = template_tags(blog_id=blog.id)
    
    for i in index_mappings:

        path_string = tpl(i.path_string, **tags.__dict__)

        master_path_string = path_string

        report.append("Index page: " + master_path_string)

        add_page_fileinfo(None, i, master_path_string,
             blog.url + "/" + master_path_string,
             blog.path + '/' + master_path_string)

    return report


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

def republish_blog(blog_id):

    import time
    begin = time.clock()

    data = []
    data.extend(["<h3>Files built:</h3><hr>"])

    blog = get_blog(blog_id)
    
    for p in blog.published_pages():
        queue_page_actions(p, True)
    
    queue_index_actions(blog)

    end = time.clock()

    data.append("Total processing time: {0:.2f} seconds.".format(end - begin))
    return data

# TODO: rework this to become a wrapper for a more general set of functions in core.queue
def process_queue(blog):
    '''
    Processes the jobs currently in the queue, for the selected blog.
    Eventually this will take ka for diff. object scopes (blog, site, etc.)
    '''
    with db.atomic():
        
        try:
            queue_control = Queue.get(Queue.blog == blog,
                Queue.is_control == True)
        except BaseException:
            raise EmptyQueueError('No control jobs found for this blog.')
        
        if queue_control.data_string is not None:
            raise QueueInProgressException("Job already running ({})".format(queue_control.data_string))
        
        queue_control.data_string = "Running"
        queue_control.save()
        
        queue = Queue.select().order_by(Queue.priority.desc(),
            Queue.date_touched.desc()).where(Queue.blog == blog,
            Queue.is_control == False).limit(MAX_BATCH_OPS)
            
        queue_length = queue.count()
        
        if queue_length > 0:
            logger.info("Queue job #{} @ {} (blog #{}, {} items) started.".format(
                queue_control.id,
                date_format(queue_control.date_touched),
                queue_control.blog.id,
                queue_length))
        
        for q in queue:
            
            try:
                job_type.action[q.job_type](q)
            except BaseException:
                raise
            else:
                remove_from_queue(q.id)
            
        queue_control = Queue.get(Queue.blog == blog,
            Queue.is_control == True)
        
        queue_control.data_integer = queue_control.data_integer - queue_length
        
        if queue_control.data_integer <= 0:
            queue_control.delete_instance()
            logger.info("Queue job #{} @ {} (blog #{}) finished.".format(
                queue_control.id,
                date_format(queue_control.date_touched),
                queue_control.blog.id))            
        else:
            queue_control.data_string = None
            queue_control.save()
            logger.info("Queue job #{} @ {} (blog #{}) continuing with {} items left.".format(
                queue_control.id,
                date_format(queue_control.date_touched),
                queue_control.blog.id,
                queue_length))
            
    return queue_control.data_integer

def purge_fileinfo(fileinfos):
    '''
    Takes a collection of fileinfos in the form of a model
    and removes them from the fileinfo list.
    Returns how many entries were purged.
    No security checks are performed.
    '''
    
    purge = DeleteQuery(FileInfo).where(FileInfo.id << fileinfos.select(FileInfo.id).tuples())
    return purge.execute()
    
    
def purge_blog(blog):
    '''
    Deletes all fileinfos from a given blog and recreates them.
    This function may also eventually be expanded to delete all the files
    associated with a given blog (except for assets)
    No security checks are performed.
    '''
    
    import time
    
    report = []
    report.append("Purging and recreating blog <b>{}</b>.".format(blog.name))
    
    begin = time.clock()
    
    fileinfos_purged = purge_fileinfo(blog.fileinfos)
    report.append("<hr/>{} file objects erased.".format(fileinfos_purged))
    pages_to_insert = blog.pages()

    for n in pages_to_insert:
        build_page_fileinfo(n.id)
        
    report.append("<hr/>{} page objects created.".format(pages_to_insert.count()))
    f_i = build_archive_fileinfo(pages_to_insert)
    report.append("{} archive objects created.".format(len(f_i)))
    
    for n in blog.index_templates:
        build_index_fileinfo(n.id)
    
    report.append("{} index objects created.".format(blog.index_templates.count()))
    end = time.clock()
    
    total_objects = pages_to_insert.count() + len(f_i) + blog.index_templates.count()
    report.append("<hr/>Total objects created: {}.".format(total_objects))
    report.append("Total processing time: {0:.2f} seconds.".format(end - begin))
    
    return report



media_filetypes = Struct()
media_filetypes.image = "Image"
media_filetypes.types = {
    'jpg':media_filetypes.image,
    'gif':media_filetypes.image,
    'png':media_filetypes.image,
    }

def register_media(filename, path, user, **ka):
    
    media = Media(
        filename=filename,
        path=path,
        type=media_filetypes.types[os.path.splitext(filename)[1][1:]],
        user=user,
        friendly_name=ka['friendly_name'] if 'friendly_name' in ka else filename
        )
    
    media.save()
    
    if 'page' in ka:
        page = ka['page']
        association = MediaAssociation(
            media=media,
            page=page,
            blog=page.blog,
            site=page.blog.site)
        
        association.save()
        
        media.blog = page.blog
        media.site = page.blog.site
        media.url = page.blog.url + page.blog.media_path + "/" + media.filename
        media.save()
    
    return media
