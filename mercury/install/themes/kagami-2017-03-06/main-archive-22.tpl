% _=module('Modules')
% img =_.placeholder()
% include('Header')
% ssi('Nav 2')
% archive_type = fileinfo.file_path.split('/')[0]
% archive_category = {'article':'Article','news':'News'}[archive_type]
<div class="section section-sm container">
  <div class="col-lg-9 col-md-9 article-body">
    <h2>{{archive_category}} Archives</h2>
% from core.models import Page
% page_list = blog.category(title=archive_category).pages.published.order_by(Page.publication_date.desc()).limit(50)    
% current_year = None    
% for n in page_list:
% if n.publication_date.year!= current_year:
% current_year = n.publication_date.year
    <h3><a href="/archive/{{archive_type}}/{{n.publication_date.year}}">{{n.publication_date.year}}</a></h3><hr/>
% end  
% include('Article Description',_=_,n=n)
% end
    <hr/>
    <h3>Continue reading archives from <a href="/archive/{{archive_type}}/{{current_year}}">{{current_year}}</a></h3>
  </div>  
  % include('Sidebar')

</div>  
% ssi('Footer')