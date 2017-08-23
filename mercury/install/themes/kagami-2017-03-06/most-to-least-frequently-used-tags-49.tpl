% from core.libs.peewee import fn, JOIN_LEFT_OUTER, SQL
% from core.models import TagAssociation, Tag
<%
   for n in blog.tags.select(Tag,
   fn.COUNT(TagAssociation.page).alias('count_page'),
   fn.COUNT(TagAssociation.media).alias('count_media'),
   ).join(TagAssociation).group_by(Tag).order_by(
   SQL('count_page').desc(),
   SQL('count_media').desc()
   ):
%>   
<p>{{n.tag}},{{n.count_page}},{{n.count_media}}
% end