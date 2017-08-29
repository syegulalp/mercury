import os, datetime

from core.utils import (generate_date_mapping)
from core.error import (ArchiveMappingFormatException, NoArchiveForFileInfo)

from core.models import (Page, TemplateMapping, TagAssociation, template_type,
    Category, PageCategory, FileInfo, template_tags, User,
    FileInfoContext)

from core.libs.peewee import IntegrityError

def eval_paths(path_string, dict_data):

    #===========================================================================
    # Failed attempt at caching, not worth it
    # try:
    #     path_obj = Cache.path_cache[path_string]
    # except KeyError:
    #     path_string = replace_mapping_tags(path_string)
    #     path_obj = compile(path_string, path_string, 'eval')
    #     Cache.path_cache[path_string] = path_obj
    #
    #===========================================================================

    path_obj = replace_mapping_tags(path_string)
    try:
        paths = eval(path_obj, dict_data)
    except Exception as e:
        paths = None
        # raise Exception('Invalid path string: {} // Data: {} // Exception: {}'.format(
            # path_string,
            # dict_data,
            # e))
    return paths

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
                template=f.xref.template,
                fileinfo=f)
        else:

            archive_pages = generate_archive_context_from_fileinfo(
                f.xref.archive_xref, blog.pages.published, f)

            # The context object we use

            tags = template_tags(blog=blog,
                template=f.xref.template,
                archive=archive_pages,
                archive_context=f,
                fileinfo=f)

    else:
        tags = template_tags(page=f.page,
            template=f.xref.template,
            fileinfo=f)

    if tags.archive is not None:
        if tags.archive.pages.count() == 0:
            raise NoArchiveForFileInfo('No archives for page {} using fileinfo {}'.format(
            f.page, f))

    return tags

def build_pages_fileinfos(pages, template_mappings=None):
    '''
    Creates fileinfo entries for the template mappings associated with
    an iterable list of Page objects.
    :param pages:
        List of page objects to build fileinfos for.
    '''

    fileinfos = []

    for n, page in enumerate(pages):

        if template_mappings is None:
            mappings = page.template_mappings
        else:
            mappings = template_mappings

        if mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for this page.')

        tags = template_tags(page=page)

        for t in mappings:

            # path_string = replace_mapping_tags(t.path_string)
            path_string = generate_date_mapping(
                page.publication_date_tz.date(), tags,
                replace_mapping_tags(t.path_string))

            # for tag archives, we need to return a list from the date mapping
            # in the event that we have a tag present that's an iterable like the tag list
            # e.g., for /%t/%Y, for a given page that has five tags
            # we return five values, one for each tag, along with the year

            if path_string == '' or path_string is None:
                continue

            # master_path_string = path_string

            fileinfos.append(
                add_page_fileinfo(page, t, path_string,
                    page.blog.url + "/" + path_string,
                    page.blog.path + '/' + path_string,
                    str(page.publication_date_tz))
                )


    return fileinfos

def build_archives_fileinfos_by_mappings(template, pages=None, early_exit=False):

    # build list of mappings if not supplied
    # if the list has no dirty mappings, exit

    # also check to make sure we're not using a do-not-publish template

    # TODO: Maybe the smart thing to do is to check the
    # underlying archive type for the template first,
    # THEN create the mappings, so we don't have to do the awkward
    # stuff that we do with tag archives


    # counter = 0
    mapping_list = {}

    if pages is None:
        pages = template.blog.pages.published

    for page in pages:
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
            # return mapping_list
            break

    fileinfo_list = []

    for n in mapping_list:
        # TODO: we should bail if there is already a fileinfo for this page?
        new_fileinfo = add_page_fileinfo(*mapping_list[n][0])
        FileInfoContext.delete().where(FileInfoContext.fileinfo == new_fileinfo).execute()
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

        new_fileinfo.mapping_sort = '/'.join(archive_context)
        new_fileinfo.save()
        fileinfo_list.append(new_fileinfo)

    return fileinfo_list

# FIXME: this should be the core of how we rework the whole thing
# rewrite the above function and below function to match, too?

'''
maybe replace $i, $C, etc. with {{blog.index}} etc.?

'''
from itertools import product

def build_archives_fileinfos_2(pages):
    '''
    Takes a page (maybe a collection of same) and produces fileinfos
    for the date-based archive entries for each
    :param pages:
        List of pages to produce fileinfos for date-based archive entries for.
    '''

    counter = 0
    mapping_list = {}

    for page in pages:
        tags = template_tags(page=page)
        if page.archive_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for the archives for this page.')
        paths = []
        for m in page.archive_mappings:
            path_string = m.path_string
            itr_b = False
            for n in m.archive_xref:
                itr_list = []
                itr = getattr(archive_functions[n], 'iterable', None)
                if itr:
                    itr_b = True
                    itr_list.append(itr)
            if itr_b:
                path_string = replace_mapping_tags(path_string)
                for n in product(itr_list):
                    p = page.proxy(*n)
                    for f in n:
                        paths.append(p, path_string.format(f.basename))
                    # note that all iterables should have a 'basename'
                    # that yields either the computed as_basename where there is no
                    # original basename, or the actual basename
                    # ????


            else:
                paths.append((page, replace_mapping_tags(path_string)))


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

    return paths, mapping_list

    '''
    for counter, n in enumerate(mapping_list):
        # TODO: we should bail if there is already a fileinfo for this page?
        new_fileinfo = add_page_fileinfo(*mapping_list[n][0])
        FileInfoContext.delete().where(FileInfoContext.fileinfo == new_fileinfo).execute()
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

        new_fileinfo.mapping_sort = '/'.join(archive_context)
        new_fileinfo.save()

    try:
        return counter + 1
    except Exception:
        return 0
    '''

def build_archives_fileinfos(pages):
    '''
    Takes a page (maybe a collection of same) and produces fileinfos
    for the date-based archive entries for each
    :param pages:
        List of pages to produce fileinfos for date-based archive entries for.
    '''

    counter = 0
    mapping_list = {}

    for page in pages:
        tags = template_tags(page=page)
        if page.archive_mappings.count() == 0:
            raise TemplateMapping.DoesNotExist('No template mappings found for the archives for this page.')
        s = []
        for m in page.archive_mappings:
            q = replace_mapping_tags(m.path_string)
            s.append(q)
            paths_list = eval_paths(m.path_string, tags.__dict__)

            if type(paths_list) in (list,):
                paths = []
                for n in paths_list:
                    if n is None:
                        continue
                    p = page.proxy(n[0])
                    # FIXME: eliminate the need for page proxies passed manually
                    # at this stage of the process we should generate those
                    # page context in one column, whatever it is, and path strings in another
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
    # raise Exception(s)
    for counter, n in enumerate(mapping_list):
        # TODO: we should bail if there is already a fileinfo for this page?
        new_fileinfo = add_page_fileinfo(*mapping_list[n][0])
        FileInfoContext.delete().where(FileInfoContext.fileinfo == new_fileinfo).execute()
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

        new_fileinfo.mapping_sort = '/'.join(archive_context)
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
                deleted_files.append(n.sitewide_file_path)
        except Exception as e:
            raise e

    return deleted_files

def delete_page_fileinfo(page):
    '''
    Deletes the fileinfo entry associated with a specific page.
    This does not delete fileinfos that are general archives.
    :param page:
        The page object remove from the fileinfo index.
    '''

    fileinfo_to_delete = FileInfo.delete().where(FileInfo.page == page)
    return fileinfo_to_delete.execute()

class ArchiveContext():
    def __init__(self, context_list, original_pageset, **ka):
        self.pages = None  # actual recordset
        self.next = None  # eventually set this as a property that returns the new object
        self.previous = None
        self.tag = None  # ?

        self.context_list = context_list

        original_page, fileinfo = None, None

        try:
            original_page = ka['page']
        except KeyError:
            try:
                fileinfo = ka['fileinfo']
            except KeyError:
                raise KeyError("A page or a fileinfo object must be provided.", Exception)

        tag_context = original_pageset

        date_counter = {
            "year":None,
            "month":None,
            "day":None
            }

        for m in context_list:
            tag_context, date_counter = archive_functions[m]["context"](
                fileinfo, original_page, tag_context, date_counter)

        # for last one get next/previous, or get them for all?

        self.pages = tag_context



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

    # TODO: Generate next/previous from last element in context list.
    # So we need next/previous year, month, day, category, etc.


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
        year_context = original_page.publication_date_tz.year
        blog = original_page.blog
    else:
        year_context = fileinfo.year
        blog = fileinfo.template_mapping.template.blog

    year_start = datetime.datetime(
        year=year_context,
        month=1,
        day=1,
        )

    year_start_tz = Page._date_to_utc(None, blog.timezone,
        year_start)

    year_end = datetime.datetime(
        year=year_context,
        month=12,
        day=31,
        hour=23,
        minute=59,
        second=59,
        )

    year_end_tz = Page._date_to_utc(None, blog.timezone,
        year_end)

    tag_context_next = tag_context.select().where(
        Page.publication_date >= year_start_tz,
        Page.publication_date <= year_end_tz
        )

    date_counter["year"] = year_context

    return tag_context_next, date_counter

# thank you: https://stackoverflow.com/a/13565185
def last_day_of_month(date):
    next_month = date.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)


def month_context(fileinfo, original_page, tag_context, date_counter):

    if date_counter["year"] is False:
        raise ArchiveMappingFormatException("An archive mapping was encountered that had a month value before a year value.", Exception)

    if fileinfo is None:
        month_context = original_page.publication_date_tz.month
        blog = original_page.blog
    else:
        month_context = fileinfo.month
        blog = fileinfo.template_mapping.template.blog

    month_start = datetime.datetime(
        year=date_counter["year"],
        month=month_context,
        day=1)

    month_start_tz = Page._date_to_utc(None, blog.timezone,
        month_start)

    month_end = datetime.datetime(
        year=date_counter["year"],
        month=month_context,
        day=last_day_of_month(month_start).day,
        hour=23,
        minute=59,
        second=59)

    month_end_tz = Page._date_to_utc(None, blog.timezone,
        month_end)


    tag_context_next = tag_context.select().where(
        Page.publication_date >= month_start_tz,
        Page.publication_date <= month_end_tz
        )

    date_counter["month"] = month_context

    return tag_context_next, date_counter


#     tag_context_next = tag_context.select().where(
#         Page.publication_date.month << month_context)
#
#     next_month_context = [(month_context[0] + 1 % 12) or 12]
#     prev_month_context = [month_context[0] - 1 or 12]
#
#     tag_context_next.next = tag_context.select().where(
#         Page.publication_date.month << next_month_context)
#
#     tag_context_next.prev = tag_context.select().where(
#         Page.publication_date.month << prev_month_context)


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
    "c":{
        "mapping":lambda x:x.context.category.category.id,
        "context":category_context,
        'format':lambda x:'{}'.format(x),
        'iterable':lambda x:x.categories,
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
        'format':lambda x:'{}'.format(x),
        'iterable':lambda x:x.tags,
        }
    }


import re

mapping_tags = (
    # Index file
    (re.compile(r'\$i'), 'blog.index_file'),
    # SSI path
    (re.compile(r'\$s'), 'blog.ssi_path'),
    # Filename for a given page
    (re.compile(r'\$f'), 'page.filename'),
    # Year/month/day mapping
    (re.compile(r'\$([Ymd])'), '\%\1'),
    # Category
    (re.compile(r'\$C'), 'page.primary_category.basename_path'),
    (re.compile(r'\$c'), '{}'),
    # Tag mapping
    # We don't actually map these; they're just detected for context, it seems.
    (re.compile(r'\$T'), '{}'),

)

def replace_mapping_tags(string):

    for n in mapping_tags:
        string = re.sub(n[0], n[1], string)

    return string





def build_mapping_xrefs(mapping_list):

    import re
    iterable_tags = (
        (re.compile('%Y'), 'Y'),
        (re.compile('%m'), 'M'),
        (re.compile('%d'), 'D'),
        (re.compile(r'\$C'), 'C'),
        (re.compile(r'\$c'), 'c'),
        # (re.compile(r'\.category\.'), 'c'),
        (re.compile(r'\$A'), 'A'),
        # (re.compile('page\.user.?'), 'A'),
        # (re.compile('page\.author.?'), 'A'),
        (re.compile(r'\$T'), 'T')
        # (re.compile('page\.tags.?'), 'T')
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
