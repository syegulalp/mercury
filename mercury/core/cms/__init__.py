from core.models import Struct, template_tags
from core.template import MetalTemplate
from core.error import PageTemplateError

class Cache():
    template_cache = {}
    blog_tag_cache = {}
    path_cache = {}
    module_cache = {}
    include_cache = {}
    # ssi_cache = {}

    @classmethod
    def clear(self):
        self.template_cache = {}
        self.blog_tag_cache = {}
        self.path_cache = {}
        self.module_cache = {}
        self.include_cache = {}
        # self.ssi_cache = {}

def invalidate_cache():
    Cache.clear()

save_action_list = Struct()

save_action_list.SAVE_TO_DRAFT = 1
save_action_list.UPDATE_LIVE_PAGE = 2
save_action_list.EXIT_EDITOR = 4
save_action_list.UNPUBLISH_PAGE = 8
save_action_list.DELETE_PAGE = 16

#===============================================================================
# We're going to phase this out in favor of
# something more explicit submitted from the front end:
# action="['save_to_draft','update_live_page']" ?
#
# Example:
# save_actions = (
#     'save_to_draft',
#     'update_live_page',
#     'exit_editor',
#     'unpublish_page',
#     'delete_page')
#===============================================================================


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
        tpx = Cache.template_cache[f.template_mapping.template.id]

    except KeyError:
        try:
            pre_tags = Cache.blog_tag_cache[tp.blog.id]
        except KeyError:
            pre_tags = template_tags(blog=tp.blog)

        Cache.blog_tag_cache[tp.blog.id] = pre_tags

        tpx = MetalTemplate(source=tp.body,
            tags=pre_tags.__dict__)
        Cache.template_cache[f.template_mapping.template.id] = tpx

    try:
        return tpx.render(**tags.__dict__)

    except Exception:
        import traceback, sys
        tb = sys.exc_info()[2]
        line_number = traceback.extract_tb(tb)[-1][1] - 1

        raise PageTemplateError("Error in template '{}': {} ({}) at line {}".format(
            tp.for_log,
            sys.exc_info()[0],
            sys.exc_info()[1],
            line_number
            ))

