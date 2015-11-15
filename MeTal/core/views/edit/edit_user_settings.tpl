% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-xs-12">

    <form class="form-horizontal" method="post">
    {{!csrf_token}}

    <div class="col-xs-12">
    % include('include/nav_tabs.tpl')
	<br/>

	</div>

    % if nav_default=='basic':
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
            <label for="user_password" class="col-sm-2 control-label">Password</label>
            <div class="col-sm-9">
                <input type="password" class="form-control" aria-describedby="user_password_help"
                value=""
                id="user_password" name="user_password">
                <span id="user_password_help" class="help-block">User's password. (Leave blank unless changing.)</span>

                <input type="password" class="form-control" aria-describedby="user_password_help"
                value=""
                id="user_password_confirm" name="user_password_confirm">
                <span id="user_password_help" class="help-block">Confirm password.</span>

            </div>
        </div>

        <div class="form-group">
            <div class="col-sm-offset-2 col-sm-9">
                <button name="submit_settings" type="submit" class="btn btn-primary">Save changes</button>
            </div>
        </div>

      % elif nav_default=='permissions':
      <div class="col-xs-12">
          % from core.auth import displayable,bitmask, displayable_list, settable
          % disp = displayable()
          <table class="table table-condensed table-striped table-hover">
          <thead><tr><th>User</th><th>Permission</th><th>Scope</th></tr></thead>
          % for n in permissions:
              <tr>
              <td>{{!n.user.for_display}}</td><td>{{disp[n.permission][0]}}</td>
              <td>
              % if n.permission & bitmask.administrate_system !=0:
              Systemwide
              % elif n.blog is not None:
              Blog: {{!n.blog.for_display}}
              % elif n.site is not None:
              Site: {{!n.site.for_display}}
              % end
              </td>
              </tr>
          % end
          </table>

          <div>
              <button name="submit_permissions" id="submit_permissions" class="btn btn-sm" type="submit">Add</button>
              <select class="input-sm" name="permission_list" id="permission_list">
                  % for n in settable()[editor_permissions[0].permission]:
                  <option value="{{n}}">{{disp[n][0]}}</option>
                  % end
              </select> permission to this user
              <span id="permission_target">
                  for
                  <select class="input-sm" name="permission_target_list" id="permission_target_list">
                      % for n in sites:
                      <option value="site-{{n.id}}">Site: {{n.for_log}}</option>
                      % end
                      % from core.models import Blog
                      % blogs = Blog.select().order_by(Blog.id)
                      % for n in blogs:
                      <option value="blog-{{n.id}}">Blog: {{n.for_log}}</option>
                      % end
                  </select>
              </span>
          </div>
      </div>

      % end

    </form>

</div>
% include('include/footer.tpl')
<script>
$('#permission_list').on('change',function()
{
	v = $(this).val();
	if (v==64)
	{
	$('#permission_target').hide();
	}
	else
	{
	$('#permission_target').show();
	}
});
</script>