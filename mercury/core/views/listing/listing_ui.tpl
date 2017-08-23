% msg_float = True
% include('include/header.tpl')
% include('include/header_messages.tpl')
% cols = colset['colset']
% include('listing/listing_ui_core.tpl')
% include('include/footer.tpl')
<script type="text/javascript" src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/activity.js"></script>
<script async src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/search.js"></script>
<script>
function submit_to_api(target)
{
	form = $('#listing_form');
	$.post(target, form.serialize()).done(function(data, textStatus, xhr){
	   $('#listing_form :checkbox:checked').each(function(){
        $(this).prop('checked', false);
        });
	   if (parseInt(xhr.getResponseHeader('X-Page-Count'))==0){
	       status_message('warning', data,
            'submit-to-api-warning',
            'warning-sign');
        }
        else
        {
            status_message('success', data,
            'submit-to-api-success',
            'ok-sign');
        }
        
	}).fail().always();
	
}
</script>