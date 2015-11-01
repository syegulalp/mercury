% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-xs-12">
<form class="form-horizontal" method="post">
{{!csrf_token}}
    <div class="form-group">
        <label for="category_title" class="col-sm-2 control-label">Category name</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="category_title_help"
            value="{{category.title}}"
            id="category_title" name="category_title">
            <span id="category_title_help" class="help-block">You can rename this category globally.</span>
        </div>
    </div>

    <div class="form-group">
        <label for="category_parent" class="col-sm-2 control-label">Parent category</label>
        <div class="col-sm-9">
        <select id="category_parent" name="category_parent" class="form-control">
            % for c in category_list:
            % disabled=''
            % if c.id==category.id:
            % disabled='disabled'
            % end
            % selected=''
            % if category.parent_category==c.id:
            % selected=' selected'
            % end
            % num=''
            % if c.id is not None:
            % num=" (#{})".format(c.id)
            % end
            <option value="{{c.id}}"{{!selected}}{{!disabled}}>{{c.title}}{{num}}</option>
            % end
        </select>
            <span id="category_parent_help" class="help-block">Choose the category that this category is organized under(if any).</span>
        </div>
    </div>

    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-9">
            <button type="submit" class="btn btn-primary">Save changes</button>
            <span class='pull-right'>
                <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/category/{{category.id}}/delete"><button type="button" name="delete" class="btn btn-danger">Delete this category</button></a>
            </span>
        </div>
    </div>

</form>
<hr/>
</div>
% include('include/footer.tpl')