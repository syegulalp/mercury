% from core.models import *
% import os
<p>{{blog.path}}/{{blog.media_path}}</p><hr/>
% oldpath = blog.path+'/'+blog.media_path+'/'
% for n in blog.pages:
<p>{{n.id}} ({{n.title}}) {{n.publication_date.year}}:</p>
% for m in n.media:
<p>{{m.id}} ({{m.filename}}, {{m.path}}, {{m.local_path}}, {{m.url}})</p>
% try:
% os.mkdir(blog.path+'/media/'+str(n.publication_date.year))
% except Exception as e:
<p>{{e}}</p>
% end
% end
<hr/>
% end

# ITerate through all pages in a given year
# For each media:
# X create the year directory if it doesn't yet exist
# move the file to the new location, if it doesn't already match
# update the media's path, local_path, and url
# save media
# push a copy of the page in question to the queue

# also - fix up youtube references
% # <div class="embed-responsive embed-responsive-16by9"><iframe class="embed-responsive-item" src="https://www.youtube.com/embed/yoI9Yl60BqU" width="560" height="315" frameborder="0" allowfullscreen="allowfullscreen"></iframe></div>