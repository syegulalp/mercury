% rebase('modal/modal_contents.tpl', title=title)
<form id="media_list" action="">
<div class="form-group">
<input name="media_id" class="form-control" id="media_id" placeholder="Media ID #">
</div>
<div class="form-group">
<button type="button" onclick="fetch_img();" class="btn btn-default">Load</button>
</div>
<input type="hidden" name="page" id="page" value="{{page.id}}">
</form>
<a href="{{settings.BASE_URL}}/blog/{{blog.id}}/media" target="_blank">See all media for this blog</a>
<script>
function fetch_img()
{
    img = $('#media_id').val();
    open_modal(global.base + "/page/" + global.page + "/get-media-templates/"+img);
}
$('[data-toggle="tooltip"]').tooltip({
        html : true
    })
</script>