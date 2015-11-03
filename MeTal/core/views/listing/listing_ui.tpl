% include('include/header.tpl')
% include('include/header_messages.tpl')
% cols = colset['colset']
% include('listing/listing_ui_core.tpl')
% include('include/footer.tpl')
<script async src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/search.js"></script>
<script>
function submit_to_api()
{
	$('#listing_table :checkbox:checked').each(function(){
		console.log(this);
		$(this).prop('checked', false);
		// add to form
		// open modal
		// submit form 
		// get results in modal 
	});
	
}
</script>