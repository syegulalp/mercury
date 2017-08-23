% _=module('Modules')
<nav class="navbar navbar-inverse navbar-fixed-top item-dek" role="navigation">
  <div class="container">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-ex1-collapse">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="navbar-brand" href="/">
        <img src="/media/ganriki-sm4.png"/>&nbsp;&nbsp;<b>Ganriki</b>&nbsp;&nbsp;<small>anime seen anew&nbsp;&nbsp;</small>
      </a>
    </div>
    <div class="collapse navbar-collapse navbar-ex1-collapse">
      <ul class="nav navbar-nav navbar-right">
        <li>
          <form id="search-form" class="form-inline" style="" role="form" method="get" action="http://www.google.com/search">
            <div class="form-group">
              <label class="sr-only" for="google-search">Site search</label>
              <input id="google-search" type="text" name="q" maxlength="255" class="form-control input-sm" placeholder="Search" data-cip-id="google-search" />
            </div>
            <button type="submit" class="btn btn-primary btn-sm">Go</button>
            <input type="hidden" name="sitesearch" value="ganriki.org"/>
          </form>
        </li>
        <li><a href="/about">About</a></li>
      </ul>
      <ul class="nav navbar-nav">
        <li id="new-articles" class="hidden-xs"><a id="new-articles-a" data-toggle="collapse" href="#newarticles" aria-expanded="false" aria-controls="newarticles">What's New</a></li>
        <li class="visible-xs"><a href="/article">What's New</a></li>
        <li class=""><a href="/article">Archives</a></li>
      </ul>
    </div>
    <div id="newarticles" class="container collapse">
      <div class="carousel carousel-new">
        <div id="articlelist" class="container">
<%
articles = blog.pages.published.order_by(_.Page.publication_date.desc())
news = articles[:3]
for x,n in enumerate(news):
	img = _.article_img(n)
%>   
          <div id="article-preview-{{x+1}}">
            <div class="col-lg-4 col-md-4 col-sm-4 portfolio-item">
              <div class="hidden-xs c-fix">
                <span class="img-caption-sm disable-text">{{img.copyright}}</span>
                <a href="{{n.permalink_dir}}"><img src="{{img.url}}" class="img-responsive img-home-portfolio"/></a>
              </div>
              <span class="label label-success pull-right"></span>
              <h3 class="item-title">{{!_.patreon(n)}}<a href="{{n.permalink_dir}}">{{!n.title}}</a></h3>
              <p class="item-subtitle">{{!n.excerpt}}</p>
            </div>
          </div>
% end          
        </div>

        <a href="javascript:" id="nextlink" class="left carousel-control"><span class="icon-prev"></span></a>
        <a href="javascript:" id="previouslink" onclick="get_articles({{articles[3].id}},1);" class="right carousel-control"><span class="icon-next"></span></a>
        <center>
          <span class="badge yellow-link"><a href="/article">See all articles</a></span>&nbsp;&nbsp;
          <span class="badge yellow-link"><a href="/anime">See all anime by title</a></span>&nbsp;&nbsp;
          <span class="badge yellow-link"><a href="javascript:{}" onclick='$("#newarticles").collapse("hide");'>Close</a></span> 
        </center>
        <br/>
      </div>
    </div>
  </div>
</nav>