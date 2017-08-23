  <h3><a href="{{page.permalink}}">{{!page.title}}</a><small> {{page.publication_date_tz.strftime('%Y/%m/%d %H:%M')}}</small></h3>
  % if page.excerpt is not None:
  <p><small><em>{{!page.excerpt}}</em></small></p>
  % end
  {{!page.paginated_text[0]}}
  % if len(page.paginated_text)>1:
  <p><a href="{{page.permalink}}#more"><span class="label label-info">Read more</span></a></p>
  % end