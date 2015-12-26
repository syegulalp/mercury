% include('Header')
<div class="container">
  <h3>Archive of all blog posts</h3><hr/>
  % for p in archive.pages:
  <p><a href="{{!p.permalink}}">{{p.title}}</a> ({{p.publication_date}})</p>
  % end
  <hr/>
</div>
% include('Footer')
