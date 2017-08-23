% if page.tags_public.count()>0:
<p>Tags:
  % for n in page.tags_public:
  <a href="{{blog.url}}/tags/{{n.as_basename}}"><span class="label label-primary">{{!n.tag}}</span></a>&nbsp;
  % end
</p>
% end