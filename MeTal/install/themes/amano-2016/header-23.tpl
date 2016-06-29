% try:
% 	page.title
% except:
% 	author = ''
%	description=blog.description
%	title = blog.name
% else:
% 	description = page.excerpt
% 	author=page.author.name
%	title=page.title
% end
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link href="/static/css/bootstrap.css" rel="stylesheet" />
    <link href="/static/css/custom.css" rel="stylesheet" />
    <link href="feed.rss" rel="alternate" type="application/rss+xml" title="{{!utils.quote_escape(blog.name)}}" />
    <meta name="generator" content="{{!utils.quote_escape(settings.PRODUCT_NAME)}}" />
    <meta name="description" content="{{!utils.quote_escape(description)}}" />
    <title>{{!title}}</title>
% if page:
    <meta name="author" content="{{!utils.quote_escape(author)}}">
    <meta property="og:title" content="{{!utils.quote_escape(title)}}" />
    <meta property="og:type" content="article"/>
    <meta property="og:url" content="{{!page.permalink}}"/>
    <script type="application/ld+json">
{
  "@context" : "http://schema.org",
  "@type" : "Article",
  "name" : "{{!utils.quote_escape(title)}}",
  "description" : "{{!utils.quote_escape(description)}}",
  "url" : "{{page.permalink}}",  
  "author" : {
    "@type" : "Person",
    "name" : "{{!utils.quote_escape(author)}}"
  },
  "datePublished" : "{{!page.publication_date}}"
}
    </script>
% end      
    </head>
<body>
{{!blog.ssi('Menu')}}