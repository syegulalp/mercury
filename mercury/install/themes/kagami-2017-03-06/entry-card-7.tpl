% _=module('Modules')
% img = _.article_img(page)
<div 
data-previous="{{getattr(page.previous_page,'id',0)}}"
data-next="{{getattr(page.next_page,'id',0)}}"
data-prev-abs="{{getattr(page.previous_page,'id',0)}}"
data-next-abs="{{getattr(page.next_page,'id',0)}}"
class="col-lg-4 col-md-4 col-sm-4 portfolio-item">
  <div class="hidden-xs c-fix">
    <span class="img-caption-sm disable-text">{{img.copyright}}</span>
    <a href="{{page.permalink_dir}}">
  <img alt="{{img.url}}" src="{{img.url}}" class="img-responsive img-home-portfolio"></a>
  </div>
  <span class="label label-success pull-right"></span>
  <h3 class="item-title">{{!_.patreon(page)}}<a href="{{page.permalink_dir}}">{{page.title}}</a></h3>
  <p class="item-dek">{{!page.excerpt}}</p>
</div>