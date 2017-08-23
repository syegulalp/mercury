% ssi('Static Header')
<%
try:
	page.title
except:
	author = ''
	description=blog.description
	title = blog.name
   	is_page=False
else:
 	description = page.excerpt
 	author=page.author.name
	title=page.title
   	is_page=True
end
	meta_title = title + " | " + blog.name
    _desc = utils.html_escape(description)  
   _author = utils.html_escape(author)
%>   
    <link href="{{blog.subdir}}feed.rss" rel="alternate" type="application/rss+xml" title="{{!utils.quote_escape(blog.name)}}" />
    <meta name="generator" content="{{!utils.html_escape(settings.PRODUCT_NAME)}}" />
    <meta name="description" content="{{!_desc}}" />
    <title>{{!meta_title}}</title>
% if is_page:
% _title =  utils.html_escape(title)
    <meta name="author" content="{{!_author}}" /> 
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@GanrikiDotOrg">
    <meta name="twitter:title" content="{{!_title}}">
    <meta name="twitter:description" content="{{!_desc}}"/>
    <meta name="twitter:image" content="{{!img.url}}"/>
    <meta property="og:type" content="article"/>
    <meta property="og:title" content="{{!_title}}" />    
    <meta property="og:url" content="{{!page.permalink_dir}}"/>
    <meta property="og:image" content="{{!img.url}}"/>
  	<meta property="og:image:width" content="854"/>
  	<meta property="og:image:height" content="480"/>
    <script type="application/ld+json">
{
  "@context" : "http://schema.org",
  "@type" : "Article",
  "name" : "{{!_title}}",
  "description" : "{{!_desc}}",
  "url" : "{{page.permalink_dir}}",  
  "author" : {
    "@type" : "Person",
    "name" : "{{!_author}}"
  },
  "datePublished" : "{{!page.publication_date}}"
}
    </script>
% else:
    <meta property="og:type" content="website"/>
    <meta property="og:title" content="{{!utils.html_escape(blog.name)}}" /> 
    <meta property="og:url" content="{{!blog.permalink}}"/>
  	<meta property="og:image" content="{{!img.url}}"/>
    <meta property="og:image:width" content="854"/>
  	<meta property="og:image:height" content="480"/>
% end
      </head>
<body>
% if is_page:  
% legacy_id = page.kv_val('legacy_id') or "{}+{}".format(utils.create_basename_core(blog.name),page.id)
  <script>
    disqus_config = function () {
    this.page.url = "{{page.permalink_dir}}";
    this.page.identifier = "{{legacy_id}}";
    };
  </script>
% end  