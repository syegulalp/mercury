% _=module('Modules')

<% img =_.article_img(page)
text = []
if page.primary_category.title=='News':
	page_list = ['',page.paginated_text[0]]
else:
	page_list = page.paginated_text
end

for n in page_list:
	text.append(_.captions(_.rep(n)))
end
%>

% include('Header')
% ssi('Nav 2')

<% try:
	author =  _.Author(page.kv_get('legacy_user').get().value)
except:
	author = page.author
end
   d_a=_.default_author[page.author.id]
author.blurb = d_a['blurb']
author.email = d_a['email']
%>   

% if page.primary_category.title!='News':

<div id="myCarousel" class="carousel">
  <div class="carousel-inner">
    <div class="item active">
      <div class="fill" style="background-image:url('{{img.url}}');background-position-y:{{img.position}}%">
        <div class="img-caption disable-text">{{img.copyright}}</div>
      </div>
    </div>
</div>
% end  
  
% if '@patreon' in page.tags_list:
% ssi('Patreon')
% end  

<div style="background-color: #f5f5f5">
  <div class="section section-sm container">
    <div class="col-xs-12">
      <h1 class="item-title even" data-even="3">{{!page.title}}</h1><h4 data-even="6" class="even-lines item-subtitle even">{{!page.excerpt}}</h4>
      <p>By <a href="mailto:{{author.email}}"><i>{{author.name}}</i></a> | <a href="{{page.permalink_dir}}">{{_.date(page.publication_date_tz)}}</a> | Share: <a href="https://www.facebook.com/sharer/sharer.php?u={{page.permalink_dir}}"><i class="fa fa-facebook-square"></i></a>&nbsp;<a href="https://twitter.com/home?status={{page.permalink_dir}}"><i class="fa fa-twitter-square"></i></a> | <span class="badge yellow-link"><a href="#disqus_thread">No comments</a></span></p>
    </div>
  </div>
</div>


<div class="section section-sm container">
  <div class="col-lg-9 col-md-9 article-body">    
    
    % try:
	% article_series = page.kv_get('Series').get().value
	% except:
	% article_series = None
	% end
    
    % if article_series:
    <div class="alert alert-info">This article is part of a series on <a href="#series"><b>{{article_series}}</b>.</a></div>
    % end
    
    % for n in page.tags_list:
	% if n in _.topic_headers:
	{{!_.topic_headers[n]}}
	% end
	% end  
    
    {{!text[0]}}
    
    % ssi('Patreon Inline')
    
    {{!text[1] if len(text)>1 else ''}}
    
    % for n in page.tags_list:
	% if n in _.topic_footers:
	{{!_.topic_footers[n]}}
	% end
	% end  

% if page.tags_public.count()>0:
<hr/>
<div class="tag-list"><h2>Topics:</h2>
% include('Tags')
</div>
% end    

<hr/>        
<h2>About the Author</h2>

    <i>{{!author.blurb}}</i>
    <hr style="clear:both"/>    
    
% ssi('Disqus')
  
  </div>
  
  % include('Sidebar')

</div>  
% ssi('Footer')