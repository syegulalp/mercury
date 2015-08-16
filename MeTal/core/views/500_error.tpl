% include('include/header_min.tpl')
<div class="container" id="error_text">
<h3>Error: {{error.exception.__class__.__name__}}</h3>
<hr/>
<p>{{error.exception}}</p>
% if settings.DEBUG_MODE:
<p>{{error}}</p>
% if error.traceback:
<hr/><h4>Traceback:</h4>
<pre>{{error.traceback}}</pre>
% end
% end
<hr/>
<center><small><i>{{settings.PRODUCT_NAME}}</i></small></center>
</div>
</body></html>