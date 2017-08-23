<?xml version="1.0" encoding="UTF-8" ?>
<% tf = "%a, %d %b %Y %H:%M:%S %z"
import datetime
dt = datetime.datetime.now()
date_now = dt.strftime(tf)
try:
 	pub_date = blog.last_n_pages(1)[0].publication_date.strftime(tf)
except:
 	pub_date = date_now
end
%>
<rss version="2.0">
   <channel>
      <title>{{!utils.xml_escape(blog.name)}}</title>
      <link>{{!blog.url}}</link>
      <description>{{!utils.xml_escape(blog.description)}}</description>
      <language>en-us</language>
      <pubDate>{{!pub_date}}</pubDate>
      <lastBuildDate>{{!pub_date}}</lastBuildDate>
      <generator>{{!settings.PRODUCT_NAME}}</generator>
      <ttl>60</ttl>
      % pages = blog.last_n_pages(7)
      % for p in pages:
      <item>
         <guid>{{!p.permalink_dir}}</guid>
         <title>{{!utils.xml_escape(p.title)}}</title>
         <link>{{!p.permalink_dir}}</link>
         <description>{{!utils.xml_escape(p.excerpt)}}</description>
         <author>{{!p.author.email}} ({{!utils.xml_escape(p.author.name)}})</author>
         <pubDate>{{!p.publication_date.strftime(tf)}}</pubDate>
      </item>
      % end
   </channel>
</rss>