%from core.utils import breaks
% nonelist = ['None','',None]
% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="col-sm-12">
    <h4>Templates for {{!blog.for_display}} / Theme: {{!blog.theme.for_display}}</h4>
    <ul class="nav nav-tabs">
    % for n,template_type in enumerate(list_items):
        <li role="presentation"{{! 'class="active"' if n==0 else ''}}>
        <a href="#t-{{n}}" role="tab" data-toggle="tab">{{template_type['title']}}</a>
        </li>  
    % end 
    </ul>
    <div class="tab-content">
    % for n,template_type in enumerate(list_items):
        <div role="tabpanel" class="tab-pane{{' active' if n==0 else ''}}" id="t-{{n}}">
            <h4>
            {{template_type['title']}} <a href="{{settings.BASE_URL}}/blog/{{blog.id}}/newtemplate/{{template_type['type']}}"><span title="Create new {{template_type['title'][:-1]}}" class="glyphicon glyphicon-plus-sign"></span></a></h4>
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
                    <td><a target="_blank" href="{{settings.BASE_URL}}/template/{{template.id}}/edit">{{template.title}}</a>
                    % def_templ = template_type.get('defaults',None)
                    % if def_templ:
                    % def_templ_str = ', '.join(def_templ)
                    % if template.default_type is not None:
                    <a href="{{settings.BASE_URL}}/template/{{template.id}}/set-default"><span title="Default template for {{template.default_type}}" class="label label-success pull-right">{{template.default_type}} default</span></a>
                    % else:
                    <span class="pull-right"><a href="{{settings.BASE_URL}}/template/{{template.id}}/set-default"><span
                    title="Set as a default archive type for {{def_templ_str}}" class="glyphicon glyphicon-edit"></span></a></span>
                    % end
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
        </div>
    % end
    </div>
</div>

<!--
<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">

    </div>
</div>
-->

% include('include/footer.tpl')
<script>

</script>
