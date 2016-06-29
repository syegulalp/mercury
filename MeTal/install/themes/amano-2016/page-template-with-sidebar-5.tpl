% include('Header')
<div class="container">
  % include('Nav')
  <div class='row'>
  <div class='col-sm-9'>
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
    <div class='col-sm-3'>
      % include('Sidebar')
    </div>
  </div>
</div>
{{!blog.ssi('Footer')}}