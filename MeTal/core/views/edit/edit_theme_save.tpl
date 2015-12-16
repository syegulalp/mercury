% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-xs-12">
<form class="form-horizontal" method="post">
{{!csrf_token}}
    <div class="form-group">
        <label for="tag_name" class="col-sm-2 control-label">Theme name</label>
        <div class="col-sm-9">
            <input type="text" class="form-control" aria-describedby="tag_name_help"
            value="{{theme_name}}"
            id="tag_name" name="tag_name">
            <span id="tag_name_help" class="help-block">Pick a name to save this theme as.</span>
        </div>
    </div>
    
    
    <div class="form-group">
        <div class="col-sm-offset-2 col-sm-9">
            <button type="submit" class="btn btn-primary">Save changes</button>
         
        </div>
    </div>
</form>
<hr/>
</div>
% include('include/footer.tpl')