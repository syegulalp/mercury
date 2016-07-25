<div class='well well-small'>
  <h4>Archives</h4>
  % for n in blog.archives('Monthly Archive'):
  % df = n.date.strftime('%B %Y')
  <a href="{{n.url}}">{{df}}</a><br/>
  % end
</div>
  