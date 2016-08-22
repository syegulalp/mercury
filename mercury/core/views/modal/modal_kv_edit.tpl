% rebase('modal/modal_contents.tpl', title=title)
<form id="edit_kv" action="">
<div class="form-group">
<input name="media_id" class="form-control" id="key" placeholder="Key" value="{{key}}">
</div>
<div class="form-group">
<input name="media_id" class="form-control" id="value" placeholder="Value" value="{{value}}">
</div>
</form>
<script>
global.kv_edit_id={{kv.id}};
</script>