% include('include/header.tpl')
% msg_float = True
% include('include/header_messages.tpl')
% include('include/modal.tpl')
<form method="post" id="main_form">{{!csrf_token}}
    <div class="col-sm-9">
        <div class="form-group">
            <input type="text" class="form-control input-lg" id="template_title" placeholder="Template title"
            name="template_title" value="{{template.title}}">
        </div>

        <div class="form-group" id="editor_div">
            <textarea name="template_body" id="template_body" class="form-control" rows="8">{{template.body}}</textarea>
        </div>
        % for m in template.mappings:
        <div class="form-group resize" id="mappings_div">
            % if m.is_default is True:
            <label for="template_mapping">Default template mapping</label>
            % end
            <div class="input-group">
                <div class="input-group-btn dropup">
                    <button type="button" class="btn btn-sm btn-info dropdown-toggle" data-toggle="dropdown" aria-expanded="false">Select predefined mapping <span class="caret"></span></button>
                    <ul class="dropdown-menu" role="menu">
                    % for n in mappings:
                      <li><a href="#">{{!n[1]}}</a></li>
                    % end
                      <li><a href="#">(<i>Custom</i>)</a></li>
                    </ul>
                </div>
                <input value="{{m.path_string}}" type="text" class="form-control input-sm" id="template_mapping_{{m.id}}" placeholder="" name="template_mapping_{{m.id}}">
            </div>
        </div>
        % end

    </div>

    <div id="sidebar" class="col-sm-3">
        <div id="sidebar_inner">
        {{!sidebar}}
        </div>
    </div>

</form>
<script>var global={base:"{{settings.BASE_URL}}",template:"{{template.id}}",blog:"{{blog.id}}",
static:"{{settings.STATIC_PATH}}",csrf:"{{!csrf}}"}
</script>
% include('include/footer.tpl')
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/codemirror.js"></script>
<link rel="stylesheet" href="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/codemirror.css">
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/xml/xml.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/editor.js"></script>
<script>
var myCodeMirror = CodeMirror.fromTextArea(document.getElementById('template_body'),{
    lineNumbers: true,
    lineWrapping: true
});
</script>