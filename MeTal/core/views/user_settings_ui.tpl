% include('header.tpl')
% include('messages_float_include.tpl')
<div class="col-xs-12">

    <form class="form-horizontal" method="post">
    {{!csrf_token}}
        <div class="form-group">
            <label for="user_name" class="col-sm-2 control-label">User name</label>
            <div class="col-sm-9">
                <input type="text" class="form-control" aria-describedby="user_name_help"
                value="{{edit_user.name}}"
                id="user_name" name="user_name">
                <span id="user_name_help" class="help-block">Name of the user for the sake of display. This is not the login name.</span>
            </div>
        </div>
        
        <div class="form-group">
            <label for="user_email" class="col-sm-2 control-label">Email</label>
            <div class="col-sm-9">
                <input type="email" class="form-control" aria-describedby="user_email_help"
                value="{{edit_user.email}}"
                id="user_email" name="user_email">
                <span id="user_email_help" class="help-block">The email address associated for this user. (Used to log in)</span>
            </div>
        </div>
        
        
        <div class="form-group">
            <div class="col-sm-offset-2 col-sm-9">
                <button type="submit" class="btn btn-primary">Save changes</button>
            </div>
        </div>
        
        <hr/>            
                    
    </form>

</div>
% include('footer.tpl')