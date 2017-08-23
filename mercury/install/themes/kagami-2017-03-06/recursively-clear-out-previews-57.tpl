<%
   import os
   for cur, _dirs, files in os.walk(blog.path):
%>
  <p>{{cur}}</p>
% for f in files:
% if '.preview' in f:
  <p>{{f}}</p>
% os.remove(os.path.join(cur, f))
% end
% end  

% end