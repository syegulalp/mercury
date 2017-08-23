%for page in archive.pages:
<p><a href="{{!page.permalink}}">{{!page.title}}</a> ({{page.publication_date_tz.strftime('%Y/%m/%d %I:%M')}})
  <br/><i><small>{{!page.excerpt}}</small></i></p>
%end
