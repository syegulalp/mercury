  <h2>{{!page.title}}</h2>
  <p>By <a href="mailto:{{!page.author.email}}">{{!page.author.name}}</a> | {{!page.publication_date}}</p><hr/>
  % #header_image = page.kv('HeaderImage').value
  {{!page.paginated_text[0]}}
  