% rebase('modal-contents.tpl', title=title)
<form id="img_template" action="">
% for t in templates:
<input type="radio" name="template" value="{{t.id}}" id="t-{{t.id}}">
<label for="t-{{t.id}}">{{t.title}}</label><br>
% end
<input type="hidden" name="media" id="media" value="{{media.id}}">
</form>