%from core.utils import breaks
% include('header.tpl')
% include('header_messages.tpl')
<div class="col-sm-9">

    % n=0
    % for template_type in list_items:
    % n+=1
    <h4>{{template_type['title']}} <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/newtemplate/{{template_type['type']}}"><span title="Create new {{template_type['title'][:-1]}}" class="glyphicon glyphicon-plus-sign"></span></a></h4>
    <table class="table table-condensed table-bordered table-hover" id="templ-{{n}}">
        <thead>
            <tr>
            <th style="width:1%"><input type="checkbox" id="check-all-{{n}}" name="check-all-{{n}}"></th>
            <th style="width:50%">Title</th>
            <th style="width:30%">Default File Mapping</th>
            <th style="width:20%">Publishing Mode</th>
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

<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">

    </div>
</div>
% include('footer.tpl')
<script>

</script>