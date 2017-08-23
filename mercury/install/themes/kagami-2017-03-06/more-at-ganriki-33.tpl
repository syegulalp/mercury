% _=module('Modules')
<div class="well">
  <h4><center>More at Ganriki</center></h4>
  <center>
    <span class="badge yellow-link"><a href="/article">See all articles</a></span>
    <span class="badge yellow-link"><a href="/anime">See all anime by title</a></span>
  </center>
  <br/>
    
    % for n in blog.pages.published.order_by(blog.pages.published[0].__class__.publication_date.desc()).limit(10):
    % img = _.article_img(n)
    <p><a href="{{n.permalink_dir}}"><img src="/media/gray.png" alt="{{img.friendly_name}}" class="img-widget lazy img-responsive" data-original="{{img.url}}" style="display: block;" /></a></p>
    % include('Article Description',_=_,n=n)    
    % end
  
    <center>
    <span class="badge yellow-link"><a href="/article">See all articles</a></span>
    <span class="badge yellow-link"><a href="/anime">See all anime by title</a></span>
  </center>

</div>