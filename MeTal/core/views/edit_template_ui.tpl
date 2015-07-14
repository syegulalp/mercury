% include('header.tpl')
% include('messages_float_include.tpl')
<form method="post" id="main_form">
{{!csrf_token}}
    <div class="col-sm-9">
    
        %#include('hiders_include.tpl')

        <div class="form-group">

            <input type="text" class="form-control input-lg" id="template_title" placeholder="Template title"
            name="template_title" value="{{template.title}}">
        </div>
        
        <div class="form-group" id="editor_div">
            <textarea name="template_body" id="template_body" class="form-control" rows="8">{{template.body}}</textarea>
        </div>
        
    <div class="form-group">
    <label for="template_mapping">Default template mapping</label>
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
	<input value="{{template.default_mapping.path_string}}" type="text" class="form-control input-sm" id="template_mapping" placeholder=""
            name="template_mapping">
	</div>
	</div>
        
        
        <button type="submit" name="save" value="1" class="btn btn-sm btn-primary">Save</button>
        <span class="pull-right">
        <button type="submit" name="save" value="2" class="btn btn-sm btn-danger">Save and regenerate pages</button>
        </span>
        <br/><br/>
    
    </div>
    
    
    <div id="sidebar" class="col-sm-3">
        <div id="sidebar_inner">
        {{!sidebar}}            
        </div>
    </div>    
    

</form>
% include('footer.tpl')
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/codemirror.js"></script>
<link rel="stylesheet" href="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/codemirror.css">
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/codemirror/xml/xml.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/editor.js"></script>
<script>
var myCodeMirror = CodeMirror.fromTextArea(document.getElementById('template_body'),{
    lineNumbers: true
});
</script>