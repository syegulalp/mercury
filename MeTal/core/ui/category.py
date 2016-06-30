from core import (auth)
from core.menu import generate_menu
from core.models import (Blog, template_tags, Category, PageCategory)
from core.models.transaction import transaction
from core.libs.bottle import (template, request, redirect)
from settings import (BASE_URL)
from . import search_context

def new_category(blog_id):

    from core.models import db
    with db.atomic() as txn:

        user = auth.is_logged_in(request)
        blog = Blog.load(blog_id)
        permission = auth.is_blog_editor(user, blog)

        category_list = [n for n in blog.categories]

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

    tpl = template('edit/category',
        category=category,
        category_list=category_list,
        menu=generate_menu('blog_new_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def delete_category(blog_id, category_id, confirm='N'):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_admin(user, blog)

    category = Category.load(category_id, blog_id=blog.id)
    auth.check_category_editing_lock(blog)

    tags = template_tags(
        blog=blog,
        user=user)

    from core.utils import Status

    if request.forms.getunicode('confirm') == user.logout_nonce:
        message = 'Category {} successfully deleted'.format(
            category.for_log)
        url = '{}/blog/{}/categories'.format(BASE_URL, blog.id)
        action = 'Return to the category listing'

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

        yes = {
                'label':'Yes, delete this category',
                'id':'delete',
                'name':'confirm',
                'value':user.logout_nonce}
        no = {
            'label':'No, return to category properties',
            'url':'{}/blog/{}/category/{}'.format(
                BASE_URL, blog.id, category.id)
            }

        tags.status = Status(
            message=message,
            type='warning',
            close=False,
            yes=yes,
            no=no
            )

    tpl = template('listing/report',
        category=category,
        menu=generate_menu('blog_delete_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

@transaction
def edit_category(blog_id, category_id):
    user = auth.is_logged_in(request)
    blog = Blog.load(blog_id)
    permission = auth.is_blog_admin(user, blog)

    category = Category.load(category_id, blog_id=blog.id)
    auth.check_category_editing_lock(blog)

    category_list = [n for n in blog.categories]

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
                new_category = Category.load(
                    category_id=new_parent_category,
                    blog=blog)
            else:
                new_category = top_level_category

            status.append(['Category <b>{}</b> was reparented to <b>{}</b>.',
                [category.title, new_category.for_log]])

        if request.forms.getunicode('default') == "Y":
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

    from core.ui_kv import kv_ui
    kv_ui_data = kv_ui(category.kv_list())

    from core import ui_mgr
    tags.sidebar = ui_mgr.render_sidebar(
            panel_set='edit_category',
            # status_badge=status_badge,
            kv_object='Category',
            kv_objectid=category.id,
            kv_ui=kv_ui_data)

    tpl = template('edit/category',
        category=category,
        category_list=category_list,
        menu=generate_menu('blog_edit_category', category),
        search_context=(search_context['sites'], None),
        **tags.__dict__)

    return tpl

