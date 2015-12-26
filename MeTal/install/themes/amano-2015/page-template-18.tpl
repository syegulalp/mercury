% include('Header')
<div class="container">
  % include('Nav')
  % include('Hed/Dek')
  % if len(page.paginated_text)>1:
    <a name="more"></a>
    {{!page.paginated_text[1]}}
  % end
  % include('Tags')
  <hr/>
  {{!blog.ssi('Comments')}}
  % include('Nav')
</div>
{{!blog.ssi('Footer')}}