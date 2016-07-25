%for p in archive.pages:
<p><a href="{{!p.permalink}}">{{!p.title}}</a> ({{p.publication_date_tz.strftime('%Y/%m/%d %I:%M')}})
  <br/><i><small>{{!p.excerpt}}</small></i></p>
%end
