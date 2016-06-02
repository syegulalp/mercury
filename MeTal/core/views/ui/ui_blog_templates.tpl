%from core.utils import breaks
% nonelist = ['None','',None]
% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-sm-9">
    <h4>Templates for {{!blog.for_display}} / Theme: {{!blog.theme.for_display}}</h4><hr/>
    % for n,template_type in enumerate(list_items):
    <h4>{{template_type['title']}} <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/newtemplate/{{template_type['type']}}"><span title="Create new {{template_type['title'][:-1]}}" class="glyphicon glyphicon-plus-sign"></span></a></h4>
    <table class="table table-condensed table-bordered table-hover" id="templ-{{n}}">
        <thead>
            <tr>
            <th style="width:1%"><input type="checkbox" id="check-all-{{n}}" name="check-all-{{n}}"></th>
            <th style="width:50%">Title</th>
            <th style="width:30%">File Mapping Expression</th>
            <th style="width:20%">Publishing Mode</th>
            </tr>
        </thead>
    % for template in template_type['data']:
        <tr>
            <td><input type="checkbox" id="check-{{template.id}}" name="check-{{template.id}}">
            <td><a href="{{settings.BASE_URL}}/template/{{template.id}}/edit">{{template.title}}</a>
            % if template.default_type is not None:
            <span title="Default template for {{template.default_type}}" class="label label-success pull-right">{{template.default_type}} default</span>
            % end
            </td>
            <td>
            % if template.templatemapping.path_string in nonelist:
            <kbd>None</kbd>
            % else:
            <code>{{!breaks(template.templatemapping.path_string)}}</code>
            % end
            </td>
            <td><span title="{{publishing_mode.description[template.publishing_mode]['description']}}"
            	class="label label-{{publishing_mode.description[template.publishing_mode]['label']}}">{{template.publishing_mode}}</span></td>
        </tr>
    % end
    </table>

    % end
</div>

<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">

    </div>
</div>
% include('include/footer.tpl')
<script>

</script>
