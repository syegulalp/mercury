% include('Header')
<div class="container">
  % include('Nav')
  % include('Hed/Dek')
  % if len(page.paginated_text)>1:
    <a name="more"></a>
    {{!page.paginated_text[1]}}
  % end
  % if page.tags.count()>0:
  <hr/>
  % include('Tags')
  % end
  <hr/>
  % ssi('Comments')
  % include('Nav')
</div>
% ssi('Footer')