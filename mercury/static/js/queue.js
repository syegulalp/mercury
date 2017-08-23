function toggle_queue_runner(update=true){
    if (typeof this == "undefined"){
        this.event.stopPropagation();
    }
    t=$('#auto_queue_run_lbl')
    if (t.html()=='ON'){
        t.html('OFF');
        global.run_queue=false;
    }
    else
    {
        t.html('ON')
        global.run_queue=true;
    }
    
    t.toggleClass('label-danger');
    
    if (update){
    $.post(global.base+'/me/setting',
        {key:'run_queue',
        value:global.run_queue,
        csrf:global.csrf}
        ).done(function(){});
    }
}

if (global.run_queue===false){
    toggle_queue_runner(false);
}