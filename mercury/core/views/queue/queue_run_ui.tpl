% include('include/header.tpl')
<div class="col-xs-12">
<h3>Publishing Queue Progress</h3>
<hr>
<div id="queue_progress">
{{!start_message}}
</div>
<hr/>
</div>
% include('include/footer.tpl')
<script async src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/editor.js"></script>
<script async src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/notify.js"></script>
<script>
function update(){

    console.log("Update");

    $.get("../../blog/"+blog_id+"/publish/progress/"+original_queue_length)
        .done(function(data){
            
            $("#queue_progress").empty().append($(data).filter('#progress_inner'));
            $('#queue_counter').empty().append($(data).filter('#queue_counter'));
            
            progress = parseInt($("#progress_bar").attr("aria-valuenow"));
            
            $('#messages_float').append($(data).filter('#messages'));
            
            if (progress<100){
                update();
            }
        }).fail(function(xhr, status, error) {
            reason = xhr.statusText;
            details = $(xhr.responseText).filter('#error_text').html();
            
            $("#queue_progress").append(details);
        });
    
}

$(window).bind("load",function(){

    blog_id = {{blog.id}}
    original_queue_length = {{original_queue_length}}
    
    console.log("Start");
    
    if (original_queue_length > 0)
    {   
        update();
    }    
    
});

</script>