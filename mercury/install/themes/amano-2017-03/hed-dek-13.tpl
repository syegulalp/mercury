  <h2>{{!page.title}}</h2>
  <p>By <a href="mailto:{{!page.author.email}}">{{!page.author.name}}</a> | <a href="{{page.permalink}}">{{!page.publication_date_tz.strftime('%Y/%m/%d %H:%M')}}</a></p><hr/>
  % #header_image = page.kv('HeaderImage').value
  {{!page.paginated_text[0]}}
  