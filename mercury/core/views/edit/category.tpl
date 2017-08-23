% include('include/header.tpl')
% msg_float = True
% include('include/header_messages.tpl')
% include('include/modal.tpl')
<div class="col-sm-9">
<form class="form-horizontal" method="post">
{{!csrf_token}}
    <div class="form-group">
        <label for="category_title" class="col-sm-2 control-label">Category name
    % if category.default is True:
    </br>
    <span class="label label-warning">Default blog category</span>
    % end
    </label>
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
            <span id="category_parent_help" class="help-block">Choose the category that this category is organized under (if any).</span>
        </div>
    </div>
    
    <div class="form-group">
        <label for="category_basename" class="col-sm-2 control-label">Category basename</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="category_basename_help"
            value="{{category.basename}}"
            id="category_basename" name="category_basename">
            <span id="category_basename_help" class="help-block">Basename for this category. This is set automatically if left blank.</span>
            <p><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/category/{{category.id}}/pages">See all pages in this category.</a></p>
        </div>
    </div>
    
    <hr/>

    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-9">
            <button type="submit" name="default" value="Y" class="btn btn-primary">Set this category as default for this blog</button>
        </div>
    </div>

    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-9">
            <button type="submit" class="btn btn-success">Save changes</button>
            <span class='pull-right'>
                <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/category/{{category.id}}/delete"><button type="button" name="delete" class="btn btn-danger">Delete this category</button></a>
            </span>
        </div>
    </div>

</form>
<hr/>
</div>
<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">
    {{!sidebar}}
    </div>
</div>
<script>var global={base:"{{settings.BASE_URL}}",category:"{{category.id}}",blog:"{{blog.id}}",
static:"{{settings.STATIC_PATH}}",csrf:"{{!csrf}}",
blog_media_path:"{{blog.media_path}}",
max_filesize:{{settings.MAX_FILESIZE}}};
</script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/activity.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/kv.js"></script>
% include('include/footer.tpl')