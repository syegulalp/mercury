<style>
html, body {
	margin:0px;
}
#preview_header {
	min-height:32px;
	padding:8px;
}
#preview_body {
	margin: 0px;
	position: absolute;
	top:32px;
	bottom:0px;
	width:100%;
}
#preview_frame{
	border:0px;
	margin:0px;
	height:100%;
	width:100%;
}	
</style>
% import settings
% include('include/header_min.tpl')
<div id="preview_header">
<a class="close_preview" href="#"><span id="close_preview_sp" class="label label-info">Click here or press X to delete preview file</span></a>
<a class="pull-right" target="_blank" href="{{page_url}}"><span class="label label-info">Launch preview in its own window</span></a>
</div>
<div id="preview_body">
<iframe src="{{page_url}}" id="preview_frame" scrolling="auto">
 <p>Your browser does not support iframes.</p>
</iframe>
</div>
</body></html>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/jquery.min.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/bootstrap.min.js"></script>
<script>
var close_url = "{{settings.BASE_URL}}/page/{{page.id}}/delete-preview"; 

function shutdown(){
	$('#close_preview_sp').html('Deleting preview file...');
	$.ajax({
	url: close_url
	}).done(function(){
		window.top.close();
	}).fail(function(){
		$('#close_preview_sp').html('Could not delete preview file.');
	}).always(function(){
	});	
}

$('.close_preview').on('click',function(e){
	shutdown();
	});
	
$(window).keypress(function(e){
	if (e.which==120){shutdown();}
});

$('#preview_frame').load(function(){
	var p_frame = $('#preview_frame').contents().find('body');

	$(p_frame).keypress(function(e){
		if (e.which==120){shutdown();}
	});
 });
</script>