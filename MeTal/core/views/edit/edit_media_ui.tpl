% include('include/header.tpl')
% msg_float = True
% include('include/header_messages.tpl')
% include('include/modal.tpl')
<div class="col-sm-9">
% include('edit/edit_media_ui_core.tpl')
<hr/>
</div>
<div id="sidebar" class="col-sm-3">
    <div id="sidebar_inner">
    {{!sidebar}}
    </div>
</div>
<script>var global={base:"{{settings.BASE_URL}}",media:"{{media.id}}",blog:"{{blog.id}}",
static:"{{settings.STATIC_PATH}}",csrf:"{{!csrf}}",
blog_media_path:"{{blog.media_path}}",
max_filesize:{{settings.MAX_FILESIZE}}};
</script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/activity.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/kv.js"></script>
% include('include/footer.tpl')