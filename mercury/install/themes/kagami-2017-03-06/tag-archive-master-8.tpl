% _=module('Modules')
% img =_.placeholder()
% include('Header')
% ssi('Nav 2')

<div class="section section-sm container">
  <div class="col-lg-9 col-md-9 article-body">
% obj = fileinfo.file_path.split('/')[0]
<h1>{{obj}}</h1><hr/>
% from core.models import Tag
% for n in blog.tags.where(Tag.tag.startswith(obj+': ')).order_by(Tag.tag).naive():
% if n.pages.published.count()>0:    
    <h3><a href="{{utils.create_basename_core(n.tag.split(': ',1)[1])}}">{{n.tag[len(obj)+2:]}}</a></h3>
% end
    % end    
  </div>
  % include('Sidebar')
</div>  
% ssi('Footer')