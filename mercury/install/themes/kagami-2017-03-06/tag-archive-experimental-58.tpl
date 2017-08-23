<!--
	Experimental template for alpha split tags
	This will work best when we have functions in a template available in __template__ or whatever
	the function is
-->
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
    <h3><a href="{{utils.create_basename_core(n.tag.split(': ')[1])}}">{{n.tag[len(obj)+2:]}}</a></h3>
% end    
  </div>
  
  % include('Sidebar')

</div>  
% ssi('Footer')