% if page.tags.count()>0:
<hr/>
<p>Tags:
  % for n in page.tags:
  <span class="label label-primary">{{!n.tag}}</span>
  % end
</p>
% end