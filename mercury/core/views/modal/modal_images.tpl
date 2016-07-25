% rebase('modal/modal_contents.tpl', title=title)
<form id="media_list" action="">
<ul>
% for t in media_list:
<li>
<a
data-toggle="tooltip" data-placement="bottom"
data-html="true"
title="<div style='background-color:white'><img style='max-height:50px;' src='{{t.preview_url}}'></div>"
href="#" 
onclick="fetch_img({{t.id}})"
id="t-{{t.id}}">{{t.friendly_name}}</a></li>
% end
</ul>
<input type="hidden" name="page" id="page" value="{{page.id}}">
</form>
<script>
function fetch_img(img)
{
    open_modal(global.base + "/page/" + global.page + "/get-media-templates/"+img);
}
$('[data-toggle="tooltip"]').tooltip({
        html : true
    })
</script>