% _=module('Modules')
% img = _.placeholder()
% include('Header')
% ssi('Nav 2')
% from core.models import Page
% article_list = blog.category(title='Article').pages.published.order_by(Page.publication_date.desc())

<div style="padding:20px;margin:0px;background-color:#d9edf7">
  <center>
    <b>Unlock great future Ganriki content! <a href="http://www.patreon.com/ganriki">Be a patron!</a></b><img alt="Patreon logo" src="/media/patreon.png" style="height:24px;margin-left:4px;" alt="Patreon" title="Patreon"/>
  </center>
</div>
<div id="myCarousel" class="carousel slide">
  <ol class="carousel-indicators">
    <li data-target="#myCarousel" data-slide-to="0" class="active"></li>
    <li data-target="#myCarousel" data-slide-to="1"></li>
    <li data-target="#myCarousel" data-slide-to="2"></li>
  </ol>
  
  <div class="carousel-inner">

<%
	carousel_articles = article_list[0:3]
	for x,n in enumerate(carousel_articles):
		img = _.article_img(n)
		active="item active" if x==0 else "item"
%>   
    
    <div class="{{active}}">
      <div class="fill" style="background-image:url('{{img.url}}');background-position-y:{{img.position}}%">
        <div class="img-caption disable-text">{{img.copyright}}</div>
      </div>
      <div class="carousel-caption">
        <h1 class="item-title">{{!_.patreon(n)}}<a data-even="3" class="even" href="{{n.permalink_dir}}">{{!n.title}}</a></h1>
        <h4 data-even="6" class="even-lines item-subtitle even">{{!n.excerpt}}</h4>
        <p><span class="badge yellow-link"><a href="{{n.permalink_dir}}#disqus_thread">No comments</a></span></p>
      </div>
    </div>

% end
  
  </div>
  <a class="left carousel-control" href="#myCarousel" data-slide="prev">
    <span class="icon-prev"></span>
  </a>
  <a class="right carousel-control" href="#myCarousel" data-slide="next">
    <span class="icon-next"></span>
  </a>  
  
</div>
  
  <div class="container">
    <div style="padding-bottom:0" class="section">
% news_list = blog.category(title='News').pages.published.order_by(Page.publication_date.desc())[:2]
      
      <div class="well portfolio-item">
        <div class="row">
       <div class="col-lg-8 col-md-8 col-sm-8 ">
        % for news in news_list:
        <h4><b><a href="{{news.permalink_dir}}">{{news.title}}</a></b></h4><p>{{!news.excerpt}}</p>
        % end
        <p><a href="/news">More news</a></p>
      </div>
          <div class="col-lg-1 col-md-1 col-sm-1"></div>

      <div style="border-left:1px solid #e3e3e3" class="col-lg-3 col-md-3 col-sm-3">
        
        % ssi('Crossroads Alpha')
        
      </div>
        </div>
      </div>

    </div>
</div>

<div class="container">      

% ssi('See all articles') 
      
<div class="row">

<%
	spotlight_articles = article_list[3:6]
	for x,n in enumerate(spotlight_articles):
		img = _.article_img(n)
%>
  <div class="col-lg-4 col-md-4 col-sm-4 portfolio-item">
    <div class="c-fix">
      <span class="img-caption-sm disable-text">{{img.copyright}}</span>
      <a href="{{n.permalink_dir}}"><img alt="{{img.friendly_name}}" data-original="{{img.url}}" src="/media/gray.png" class="lazy img-responsive img-home-portfolio"/></a>
    </div>
    <span class="label label-success pull-right"></span>
    <h3 class="item-title"> <a href="{{n.permalink_dir}}">{{!n.title}}</a></h3>
    <p><span class="badge yellow-link"><a href="{{n.permalink_dir}}#disqus_thread">No comments</a></span></p>
    <p class="item-dek">{{!n.excerpt}}</p>
  </div>        

% end          

  </div><!-- /.row -->

</div><!-- /.container -->

% ssi('See all articles') 

<%
feature_articles = article_list[6:9]
section = ('section-colored','section')
for x,n in enumerate(feature_articles):
img = _.article_img(n)
opening = _.rep_excerpt(n.paginated_text[0])
%>
<div class="{{section[x%2]}}">
  <div class="container">
    <div class="row">

% if x%2==0:      
      <div class="col-lg-6 col-md-6 col-sm-6">
        <div class="c-fix">
          <span class="img-caption-sm disable-text">{{img.copyright}}</span>
          <a href="{{n.permalink_dir}}"><img alt="{{img.friendly_name}}" data-original="{{img.url}}" src="/media/gray.png" class="lazy img-responsive img-home-portfolio"/></a>
        </div>
      </div>
% end
      <div class="col-lg-6 col-md-6 col-sm-6">
        <h2 class="item-title"><a href="{{n.permalink_dir}}">{{!n.title}}</a></h2>
        <h4 class="item-dek">{{!n.excerpt}}</h4>
        <p><span class="badge yellow-link"><a href="{{n.permalink_dir}}#disqus_thread">No comments</a></span></p>
        {{!_.rep(opening)}}
        <p><a href="{{n.permalink_dir}}"><i>Continue reading</i></a></p>          
      </div>
% if x%2!=0:  
      <div class="col-lg-6 col-md-6 col-sm-6">
        <div class="c-fix">
          <span class="img-caption-sm disable-text">{{img.copyright}}</span>
          <a href="{{n.permalink_dir}}"><img alt="{{img.friendly_name}}" data-original="{{img.url}}" src="/media/gray.png" class="lazy img-responsive img-home-portfolio"/></a>
        </div>
      </div>
% end
    </div>
  </div>
</div>

% end
    
% ssi('See all articles') 

</div>

% ssi('Footer') 