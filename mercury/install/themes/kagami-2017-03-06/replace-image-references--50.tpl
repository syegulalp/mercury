% from core.error import PageNotChanged
% for n in blog.media:
% n.path=n.path.replace('/home/genjipre/ganriki/assets/','/home/genjipre/g3/media/')
% n.url=n.url.replace('/assets/','/media/')
% n.url=n.url.replace('beta.ganriki.org/','www.ganriki.org/')
% n.save()
<p>{{n.filename}}|{{n.path}}|{{n.local_path}}|{{n.url}}</p>
% end

% for n in blog.pages:
% n.text = n.text.replace('beta.ganriki.org/','www.ganriki.org/')
% n.text = n.text.replace('ganriki.org/assets/','ganriki.org/media/')
% try:
% n.save(n.user)
% except PageNotChanged:
% pass
% end
<p>{{n.id}}|{{n.title}}</p>
% end
