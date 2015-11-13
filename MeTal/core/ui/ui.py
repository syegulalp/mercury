from core import (auth)
from core.menu import generate_menu

from core.models import (get_blog,
    template_tags, get_page, Page, Tag, get_category)

from core.models.transaction import transaction

from core.libs.bottle import (template, request, redirect)

from settings import (BASE_URL)

import json

queue_selections = (
    ('Remove from queue', '1', ''),
    ('Change queue priority', '2', '')
    )

common_archive_mappings = (
    ('%Y/%m/{{blog.index_file}}', 'Yearly/monthly archive'),
    ('%Y/{{blog.index_file}}', 'Yearly archive'),
    ('{{page.user.name}}/{{blog.index_file}}', 'Author archive'),
    ('{{page.user.name}}/%Y/%m/{{blog.index_file}}', 'Author/yearly/monthly archive'),
    ('{{page.user.name}}/%Y/{{blog.index_file}}', 'Author/yearly archive'),
    ('{{page.primary_category.title}}/{{blog.index_file}}', 'Category archive'),
    ('{{page.primary_category.title}}/%Y/%m/{{blog.index_file}}', 'Category/yearly/monthly archive'),
    ('{{page.primary_category.title}}/%Y/{{blog.index_file}}', 'Category/yearly archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/{{blog.index_file}}', 'Category/author archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/%Y/%m/{{blog.index_file}}', 'Category/author/yearly/monthly archive'),
    ('{{page.primary_category.title}}/{{page.user.name}}/%Y/{{blog.index_file}}', 'Category/author/yearly archive'),
    )

common_page_mappings = (
    ('{{page.basename}}/{{blog.index_file}}', '{{page.basename}}/{{blog.index_file}}'),
    ('{{page.basename}}.{{blog.base_extension}}', '{{page.basename}}.{{blog.base_extension}}')
    )

common_index_mappings = (
    ('{{blog.index_file}}', 'Default index file type for blog'),
    )

template_mapping_index = {
    'Index':common_index_mappings,
    'Page':common_page_mappings,
    'Archive':common_archive_mappings,
    'Include':(),
    'Media':(),
    'System':()
    }

search_context = (
    {'blog':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id),
            'form_description':'Search entries:',
            'form_placeholder':'Entry title, term in body text'},
    'blog_media':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/media",
            'form_description':'Search media:',
            'form_placeholder':'Media title, term in description, URL, etc.'},
    'blog_templates':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/templates",
            'form_description':'Search templates:',
            'form_placeholder':'Template title or text in template'},
    'site':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search blogs:',
            'form_placeholder':'Page title or text in description'},
    'sites':
            {'form_target':lambda x: BASE_URL,  # @UnusedVariable
            'form_description':'Search sites:',
            'form_placeholder':'Site title or text in description'},
    'blog_queue':
            {'form_target':lambda x: BASE_URL + "/blog/" + str(x.id) + "/queue",
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
    'site_queue':
            {'form_target':lambda x: BASE_URL + "/site/queue",  # @UnusedVariable
            'form_description':'Search queue:',
            'form_placeholder':'Event ID, page title, etc.'},
     'system_log':
            {'form_target':lambda x: BASE_URL + "/system/log",  # @UnusedVariable
            'form_description':'Search log:',
            'form_placeholder':'Log entry data, etc.'}
    }
    )

submission_fields = ('title', 'text', 'tag_text', 'excerpt')

status_badge = ('', 'warning', 'success', 'info')

save_action = (
    (None),
    (1, 'Save draft'),
    (3, 'Save & update live'),
    (1, 'Save draft')
    )



@transaction
def register_plugin(plugin_path):
    from core.plugins import register_plugin, PluginImportError
    try:
        new_plugin = register_plugin(plugin_path)
    except PluginImportError as e:
        return (str(e))
    return ("Plugin " + new_plugin.friendly_name + " registered.")


media_buttons = '''
<button type="button" id="modal_close_button" class="btn btn-default" data-dismiss="modal">Close</button>
<button type="button" {} class="btn btn-primary">{}</button>
'''

def new_category(blog_id):

    from core.models import db
    with db.atomic() as txn:

        user = auth.is_logged_in(request)
        blog = get_blog(blog_id)
        permission = auth.is_blog_editor(user, blog)

        category_list = [n for n in blog.categories]

        from core.models import Category

        category = Category(id=0,
            title='',
            blog=blog)

        top_level_category = Category(
            id=None,
            title='[Top-level category]',
            parent=None
            )

        category_list.insert(0, top_level_category)

        tags = template_tags(
            blog=blog,
            user=user)

    if request.method == "POST":
        with db.atomic() as txn:
            category_title = request.forms.getunicode('category_title')
            try:
                parent_category = int(request.forms.getunicode('category_parent'))
            except ValueError:
                parent_category = None

            with db.atomic() as txn:

                category = Category(blog=blog,
                    title=category_title,
                    parent_category=parent_category
                    )
                category.save()

        redirect('{}/blog/{}/category/{}'.format(
            BASE_URL, blog.id, category.id))

    tpl = template('edit/edit_category_ui',
        category=category,
        category_list=category_list,
        menu=generate_menu('new_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def delete_category(blog_id, category_id, confirm='N'):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    category = get_category(blog=blog, category_id=category_id)
    auth.check_category_editing_lock(blog)

    tags = template_tags(
        blog=blog,
        user=user)

    from core.utils import Status

    if confirm == 'Y':
        message = 'Category {} successfully deleted'.format(
            category.for_log)
        url = '{}/blog/{}/categories'.format(BASE_URL, blog.id)
        action = 'Return to the category listing'

        from core.models import Category, PageCategory

        reparent_categories = Category.update(
            parent_category=category.parent_category).where(
                Category.parent_category == category)
        reparent_categories.execute()

        delete_category = PageCategory.delete().where(
            PageCategory.category == category.id)
        delete_category.execute()

        category.delete_instance()

        tags.status = Status(
            type='success',
            message=message,
            action=action,
            url=url,
            close=False)

    else:
        message = ('You are about to delete category <b>{}</b> from blog <b>{}</b>.'.format(
            category.for_display,
            blog.for_display))

        from core.models import Struct
        confirmation = Struct()

        confirmation.yes = {
                'label':'Yes, delete this category',
                'id':'delete',
                'name':'confirm',
                'value':'Y'}
        confirmation.no = {
            'label':'No, return to category properties',
            'url':'{}/blog/{}/category/{}'.format(
                BASE_URL, blog.id, category.id)
            }

        tags.status = Status(
            message=message,
            type='warning',
            close=False,
            confirmation=confirmation
            )

    tpl = template('listing/report',
        category=category,
        menu=generate_menu('delete_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def edit_category(blog_id, category_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
    permission = auth.is_blog_admin(user, blog)

    category = get_category(blog=blog, category_id=category_id)
    auth.check_category_editing_lock(blog)

    category_list = [n for n in blog.categories]

    from core.models import Category

    top_level_category = Category(
        id=None,
        title='[Top-level category]',
        parent=None
        )

    category_list.insert(0, top_level_category)

    tags = template_tags(
        blog=blog,
        user=user)

    from core.utils import Status
    status = []

    if request.method == "POST":
        new_category_title = request.forms.getunicode('category_title')
        old_category_title = category.title

        if new_category_title != old_category_title:

            category.title = new_category_title
            category.save()

            status.append(
                ['Category <b>{}</b> was renamed to <b>{}</b>.',
                [old_category_title, new_category_title]])

        old_parent_category = category.parent_category
        try:
            new_parent_category = int(request.forms.getunicode('category_parent'))
        except ValueError:
            new_parent_category = None

        if old_parent_category != new_parent_category:
            category.parent_category = new_parent_category
            category.save()

            if new_parent_category is not None:
                new_category = get_category(
                    category_id=new_parent_category,
                    blog=blog)
            else:
                new_category = top_level_category

            status.append(['Category <b>{}</b> was reparented to <b>{}</b>.',
                [category.title, new_category.for_log]])

        if request.forms.getunicode('default') == "Y":
            print ("Y")
            clear_default_categories = Category.update(
                default=False).where(
                    Category.blog == blog,
                    Category.default == True)
            clear_default_categories.execute()
            category.default = True
            category.save()

            status.append(['Category <b>{}</b> was set to default for blog <b>{}</b>.',
                [category.title, blog.for_log]])

    if len(status) > 0:
        message = ''
        vals = []
        for n in status:
            message += n[0]
            for m in n[1]:
                vals.append(m)
            vals.append('{}/blog/{}/purge'.format(BASE_URL, blog.id))
        tags.status = Status(type='success',
            message=message + '<br/><a href="{}">Purge and republish this blog</a> to make these changes take effect.',
            vals=vals)

    tpl = template('edit/edit_category_ui',
        category=category,
        category_list=category_list,
        menu=generate_menu('edit_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl



@transaction
def edit_tag(blog_id, tag_id):
    user = auth.is_logged_in(request)
    blog = get_blog(blog_id)
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
        menu=generate_menu('edit_tag', tag),
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
def make_tag_for_page(blog_id=None, page_id=None):

    user = auth.is_logged_in(request)

    if page_id is None:
        page = Page()
        blog = get_blog(blog_id)
        permission = auth.is_blog_editor(user, blog)
    else:
        page = get_page(page_id)
        blog = page.blog
        permission = auth.is_page_editor(user, page)

    tag_name = request.forms.getunicode('tag')

    if len(tag_name) < 1:
        return None

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
