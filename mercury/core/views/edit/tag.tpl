% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-xs-9">
<form class="form-horizontal" method="post">
{{!csrf_token}}
    <div class="form-group">
        <label for="tag_name" class="col-sm-2 control-label">Tag name</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="tag_name_help"
            value="{{tag.tag}}"
            id="tag_name" name="tag_name">
            <span id="tag_name_help" class="help-block">You can rename this tag globally.</span>
            % t=tag.pages.count()
            % if t>0:
            <p><a href="{{tag.id}}/pages"><span class="label label-info">See {{t}} page(s) that use this tag.</span></a></p>
            % else:
            <p>[<i>No pages use this tag.</i>]</p>
            % end
        </div>
    </div>
    <hr/>
    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-9">
            <span class='pull-right'>
                <a href="{{settings.BASE_URL}}/blog/{{tag.blog.id}}/tag/{{tag.id}}/delete"><button type="button" name="delete" class="btn btn-danger">Delete this tag</button></a>
            </span>
            <button type="submit" class="btn btn-success">Save changes</button>
        </div>
    </div>
</form>
<hr/>
</div>
<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">
    </div>
</div>
% include('include/footer.tpl')