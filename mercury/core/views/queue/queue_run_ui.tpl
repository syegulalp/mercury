% include('include/header.tpl')
<div class="col-xs-12">
<h3>{{!title}}</h3>
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

    $.get(action_url)
        .done(function(data){
            
            $("#queue_progress").empty().append($(data).filter('#progress_inner'));
            $('#queue_counter').replaceWith($(data).filter('#queue_counter'));
            
            progress = parseInt($("#progress_bar").attr("aria-valuenow"));
            
            $('#messages_float').append($(data).filter('#messages'));
            
            if (window.opener)
            {
                window.opener.$('#queue_counter').replaceWith($(data).filter('#queue_counter'));
            }
            
            if (progress<100){
                update();
            }
            else
            {
                if (window.opener)
                {
                    window.close();
                }
            }
                        
            
        }).fail(function(xhr, status, error) {
            reason = xhr.statusText;
            details = $(xhr.responseText).filter('#error_text').html();
            
            $("#queue_progress").append(details);
        });
    
}

$(window).bind("load",function(){

    blog_id = {{blog.id}}
    start = {{start}}
    action_url="{{!action_url}}"
    
    console.log("Start");
    
    if (start > 0)
    {   
        update();
    }    
    
});

</script>