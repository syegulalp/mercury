% include('include/header_min.tpl')
<div class="container" id="error_text">
<div id="error_header">
<h3>Error: {{error.exception.__class__.__name__}}</h3>
{{error.exception.args[0]}}
<hr/>
</div>
% if settings.DEBUG_MODE:
<div id='error_scrollable' style='overflow-y:scroll'>
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
<script>
pos1 = $('#error_header').innerHeight();
pos2 = $('#error_scrollable').offset().top;
$('#error_scrollable').height(window.innerHeight-pos1-pos2-32);
</script>
</div>
</body></html>