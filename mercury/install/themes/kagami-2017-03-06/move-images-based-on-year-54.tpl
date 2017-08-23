<%
   for n in blog.pages:
       year=n.publication_date.year
       for m in n.media:
           
%>
  <p>{{m.path}}</p>
% end  
% end  