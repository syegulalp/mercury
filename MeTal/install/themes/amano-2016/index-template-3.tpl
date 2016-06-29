% page_title = blog.name
% include('Header')
<div class="container">
  <h4>{{blog.description}}</h4>
  % for p in blog.last_n_pages(7):
  <hr/>
  <h3><a href="{{p.permalink}}">{{!p.title}}</a><small> {{p.publication_date_tz.strftime('%Y/%m/%d %H:%M')}}</small></h3>
  % if p.excerpt is not None:
  <p><small><em>{{!p.excerpt}}</em></small></p>
  % end
  {{!p.paginated_text[0]}}
  % if len(p.paginated_text)>1:
  <p><a href="{{p.permalink}}"><span class="label label-info">Read more</span></a></p>
  % end
  % end
  <hr/>
  <h4><a href="{{blog.date_archive.default_url}}">See all previous posts</a><br/>&nbsp;</h4>
</div>
{{!blog.ssi('Footer')}}