% include('header.tpl')
% include('header_messages.tpl')
<div class="col-xs-12">
% include('list_nav.tpl')

<div style="width:100%; padding-bottom:8px;border-bottom: 1px solid rgb(221,221,221)">
</div>

    <fieldset>
        <table class="table table-condensed table-striped table-hover" style="margin-bottom:0px">
            <thead>
                <tr>
                <th style="width:1%"><input type="checkbox" id="check-all" name="check-all" onclick="$(this).closest('fieldset').find(':checkbox').prop('checked', this.checked);"></th>
                <th style="width:1%">ID</th>
                <th style="width:auto">User name</th>
                </tr>
            </thead>
        % for user in user_list.iterator(): 
            <tr class="overflow">
                <td><input type="checkbox" id="check-{{user.id}}" name="check-{{user.id}}">
                <td>{{user.id}}</td>
                <td class="overflow">
                % if blog:
                <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/user/{{user.id}}">{{user.name}}</a>
                % else:
                <a href="{{settings.BASE_URL}}/site/{{site.id}}/user/{{user.id}}">{{user.name}}</a>                
                % end
                </td>
            </tr>
        % end
        </table>
    </fieldset>

<div style="width:100%; padding-top:8px;border-top: 1px solid rgb(221,221,221)">
</div>
% include('list_nav.tpl')
<br/>    
</div>
% include('footer.tpl')