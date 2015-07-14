%from core.utils import breaks
% include('header.tpl')
% include('header_messages.tpl')
<div class="col-xs-12">

    % for template_type in list_items:
    <h4>{{template_type['title']}} <span title="Create new {{template_type['title'][:-1]}}" class="glyphicon glyphicon-plus-sign"></span></h4>
    <table class="table table-condensed table-bordered table-hover">
        <thead>
            <tr>
            <th style="width:1%"><input type="checkbox" id="check-all" name="check-all"></th>
            <th style="width:33%">Title</th>
            <th style="width:33%">Default File Mapping</th>
            <th style="width:33%">Publishing Mode</th>
            </tr>
        </thead>
    % for template in template_type['data']:
        <tr>
            <td><input type="checkbox" id="check-{{template.id}}" name="check-{{template.id}}">
            <td><a href="{{settings.BASE_URL}}/template/{{template.id}}/edit">{{template.title}}</a></td>
            <td><code>{{!breaks(template.templatemapping.path_string)}}</code></td>
            <td><span title="{{publishing_mode[template.publishing_mode]['description']}}" class="label label-{{publishing_mode[template.publishing_mode]['label']}}">{{template.publishing_mode}}</span></td>
        </tr>
    % end
    </table>
    
    % end
</div>
% include('footer.tpl')