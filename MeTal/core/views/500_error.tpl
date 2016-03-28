% include('include/header_min.tpl')
<div class="container" id="error_text">
<div id="error_header">
<h3>Error: {{error.exception.__class__.__name__}}</h3>
% if error.exception.args:
{{error.exception.args[0]}}
% end
<hr/>
</div>
% if settings.DEBUG_MODE:
<div id='error_scrollable'>
<h4>Exception details:</h4>
<pre>{{error.exception}}</pre>
<hr/><h4>Error details:</h4>
<pre>{{error}}</pre>
% if error.traceback:
<hr/><h4>Traceback:</h4>
<pre>{{error.traceback}}</pre>
</div>
% end
% end
<div id='error_footer'>
<hr/>
<center><small><i>{{settings.PRODUCT_NAME}}</i></small></center>
</div>
<script></script>
</div>
</body></html>