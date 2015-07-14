% from core.utils import breaks
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
                <th style="width:5%">Media</th>
                <th style="width:1%">Title</th>
                <th style="width:1%">Author</th>
                <th style="width:1%">Created</th>
                
                </tr>
            </thead>
        % for media in media_list.iterator(): 
            <tr class="overflow">
                <td><input type="checkbox" id="check-{{media.id}}" name="check-{{media.id}}">
                <td>{{media.id}}</td>
                <td><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/media/{{media.id}}/edit"><img style="max-height:50px" src="{{media.preview_url}}"></a></td>
                <td><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/media/{{media.id}}/edit">{{media.friendly_name}}</a></td>
                <td>{{media.user.name}}</td>
                <td>{{media.created_date}}</td>
                
            </tr>
        % end
        </table>
    </fieldset>
    


<div style="width:100%; padding-top:8px;border-top: 1px solid rgb(221,221,221)">
</div>

% include('list_nav.tpl')
<br>    
</div>
% include('footer.tpl')