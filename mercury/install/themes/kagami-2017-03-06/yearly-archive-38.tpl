% _=module('Modules')
% img =_.placeholder()
% include('Header')
% ssi('Nav 2')
<% archive_type = fileinfo.file_path.split('/')[1]
	archive_category = {'article':'Article','news':'News'}[archive_type]
	from core.models import Page
	page_list = blog.category(title=archive_category).pages.published.where(
		Page.publication_date.year==archive.year).order_by(
        Page.publication_date.desc())
%>   
<div class="section section-sm container">
  <div class="col-lg-9 col-md-9 article-body">
    <h2><a href="/{{archive_type}}">{{archive_category}}</a> Archives: {{archive.year}}</h2><hr/>
% for n in page_list:
% include('Article Description')
% end
    <hr/>
    % if blog.category(title=archive_category).pages.published.where(Page.publication_date.year==(archive.year-1)).count()>0:
    <h3>See {{archive_category}} archives for <a href="../{{archive.year-1}}">{{archive.year-1}}</a>
    % else:
      <p>(<i>No earlier articles in this category.</i>)</p>
    % end
  </div>
  % include('Sidebar')

</div>  
% ssi('Footer')