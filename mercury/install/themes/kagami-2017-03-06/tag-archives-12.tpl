% _=module('Modules')
% ssi('Static Header')
% ssi('Nav 2')

<div class="section section-sm container">
  <div class="col-lg-9 col-md-9 article-body">

% tag = archive.tag.tag
% if tag is not None:    
% tag= tag.split(": ")
    <h1><a href="/{{tag[0]}}">{{tag[0]}}</a>: {{tag[1]}}</h1><small><a href="alpha/">See in alphabetical order</a></small><hr/>
% current_year = None
% for n in archive.tag.pages.published.order_by(archive.tag.pages[0].__class__.publication_date.desc()).naive():
% if n.publication_date.year!= current_year:
% current_year = n.publication_date.year
    <h3>{{n.publication_date.year}}</h3><hr/>
% end
% include('Article Description')
% end
% end

  </div>
  
  % include('Sidebar')

</div>  

% ssi('Footer')