% if 'article_series' in locals() and article_series:
<a name="series"></a>
<div id="series-box" class="well no-ol-indent">
  <h4><center><b>{{article_series}}</b></center></h4>
% _ = page.__class__
% series_objs = [x.objectid for x in _.kv_get('Series',article_series)]
% series_pages = blog.pages.published.where(_.id << series_objs).order_by(_.publication_date.asc())
<small>
<ol>
% from core import cms  
% for x, pp in enumerate(series_pages):
  % if pp.id == page.id:
  <li><b><a href="{{pp.permalink_dir}}">{{pp.title}}</a></b></li>
  % if x>0:
  % cms.queue_page_actions((series_pages[x-1],),True,True)
  % end
  % else:
  <li><a href="{{pp.permalink_dir}}">{{pp.title}}</a></li>
  % end
% end
</ol>
</small></div>  
% end