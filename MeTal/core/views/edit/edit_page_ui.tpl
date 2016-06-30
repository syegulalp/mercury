% include('include/header.tpl')
% msg_float = True
% include('include/header_messages.tpl')
% include('include/modal.tpl')
<link rel="stylesheet" href="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/css/bootstrap-datetimepicker.min.css" />
<form method="post" id="main_form">
{{!csrf_token}}
    <input type="hidden" id="page_id" name="page_id" value="{{page.id}}">
    <input type="hidden" id="blog_id" name="blog_id" value="{{blog.id}}">

    <div id="main_bar" class="col-sm-9">
	    <div class="form-group">

	            <input type="text" class="form-control input-lg entersubmit unsaved" id="page_title" placeholder="Page title"
	            name="page_title" value="{{page.title}}">

	    </div>

	    <div class="form-group" id="editor_div">

	       <textarea name="page_text" id="page_text" class="form-control unsaved editor">{{page.text}}</textarea>

	    </div>

	    <!--
	    <div class="form-group">
	        <label id="page_text_label" for="page_tag_text">Tags</label>
	        <div name="page_tag_text" id="page_tag_text" class="" contenteditable="true"></div>
	    </div>
	    -->

	    <div class="form-group resize">
	        <label id="page_text_label" for="page_excerpt">Excerpt</label>
	        <textarea name="page_excerpt" id="page_excerpt" class="form-control unsaved" rows="4">{{page.excerpt}}</textarea>
	    </div>

	    <div id="plugin_zone" class=""></div>

    </div>

    <div id="sidebar" class="col-sm-3">
        <div id="sidebar_inner">
        {{!sidebar}}
        </div>
    </div>


<hr/>
</form>
<script>var global={base:"{{settings.BASE_URL}}",page:"{{page.id}}",blog:"{{blog.id}}",
static:"{{settings.STATIC_PATH}}",csrf:"{{!csrf}}",
blog_media_path:"{{blog.media_path}}",
max_filesize:{{settings.MAX_FILESIZE}}}
global.html_editor_settings={{!html_editor_settings}};
</script>
% include('include/footer.tpl')
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/tinymce/tinymce.min.js"></script>
<script type="text/javascript" src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/moment.min.js"></script>
<script type="text/javascript" src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/bootstrap-datetimepicker.min.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/upload.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/typeahead/typeahead.bundle.min.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/tags.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/activity.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/kv.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/editor.js"></script>
