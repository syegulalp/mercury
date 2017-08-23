<div class="col-lg-3 col-md-3 article-sidebar">
  
  % include('Article Series')
  
  <div class="well">
  % ssi('Crossroads Alpha')
  </div>
  
  % try:
  % products = page.kv_get('Amazon').get().value
  % except:
  % products = None
  % end
  
  % try:
  % links = page.kv_get('Links').get().value
  % except:
  % links = None
  % end  
  
  % if products is not None:
  <div class="well">
    <center>
      <h4>Related Products</h4>
    <small><p>Product purchases<br/>support their creators<br/>and this site.</p></small>
      % for n in products.split(','):
          % if n!='':
      <span class="amazon-product"><a href="http://www.amazon.com/dp/{{n}}/?tag=thegline"><img class="img img-responsive" border="0" src="//ws-na.amazon-adsystem.com/widgets/q?_encoding=UTF8&MarketPlace=US&ASIN={{n}}&ServiceVersion=20070822&ID=AsinImage&WS=1&Format=_SL250_&tag=thegline"/></a><img src="//ir-na.amazon-adsystem.com/e/ir?t=thegline&l=am2&o=1&a={{n}}" width="1" height="1" border="0" alt="" style="border:none !important; margin:0px !important;"/></span>
          %end
      % end
      </center>
  </div>
  % end 
  
  % if links is not None:
  % import ast
  % link_list = ast.literal_eval(links)
  <div class="well">
    <h4>More about this item at...</h4>
    <ul>
    % for n in link_list:
    % if n!=[]:
      <li><a target="_blank" href="{{n[1]}}">{{!n[0]}}</a></li>
    % end
    % end
      </ul>
  </div>
  % end  

  % ssi('More At Ganriki')
  
  % ssi('Twitter')
  
</div>