% include('include/header.tpl')
% msg_float = True
% include('include/header_messages.tpl')
% include('include/modal.tpl')
% archive_default_list = archive_defaults[template.template_type]
<div class="col-xs-12">
<form method="post" id="main_form">{{!csrf_token}}
    <h3>Set {{!template.for_display}} as archive default for ...</h3>
    % is_set = False
    % for n in archive_default_list:
    % if template.default_type==n:
    % checked=" checked"
    % is_set = True
    % else:
    % checked=""
    % end
    <div class="radio">
    <label>
    <input type="radio" name="template" id="{{!n}}" value="option1"{{checked}}>
    {{!n}}
    </label>
    </div>
    % end
    % if is_set is True: #if len(archive_default_list)<=1:
    <p>(To stop using this template entirely as an archive default,
<a href="{{settings.BASE_URL}}/blog/{{blog.id}}/templates">pick another template</a>
and set that as the default for this archive type.)
    % end
    <hr/>
    <button class='btn btn-primary'>Set default</button>
</form>
</div>
% include('include/footer.tpl')