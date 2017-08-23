% for n in blog.tags:
% if n.tag.startswith('anime: '):
% stub='title: '+n.tag.split('anime: ')[1]
<p>{{stub}}</p>
<%
   # n.tag=stub
   # n.save()
%>   
% end
% end

  export to backup first
  rename tags  
  update template mappings:
  	http://cms.genjipress.com/template/1483/edit
  rebuild everything
  delete old /anime directory
  change htaccess to remap? optional
  clean out dead tags from import
   