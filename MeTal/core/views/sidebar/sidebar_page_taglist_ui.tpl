<div id="tag_list">
% if page.tags_all.count()>0:
% for tag in page.tags_all:
{{!tag.for_display}}
% end
% end
</div>