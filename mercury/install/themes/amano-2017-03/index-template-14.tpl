% page_title = blog.name
% include('Header')
<div class="container">
  <h4>{{blog.description}}</h4>
  <hr/>
  % for page in blog.last_n_pages(7):
  % include('Archive page description (full)')
  <hr/>
  % include('Tags')
  <hr class='entry-separator'/>
  % end
  <h4><a href="{{blog.date_archive.default_url}}">See all previous posts</a><br/>&nbsp;</h4>
</div>
% ssi('Footer')