<div id="tag_list">
% if page.tags.count()>0:
% for tag in page.tags:
{{!tag.for_display}}
% end
% end
</div>