
function drag_leave_event(event)
{
    event.stopPropagation();
    event.preventDefault();
    $(".uploadarea").css('background-color','');
    
}


function drag_enter_event(event)
{
    event.stopPropagation();
    event.preventDefault();
    event.originalEvent.dataTransfer.dropEffect="copy";
    $(".uploadarea").css('background-color','#ffa0a0');
    
}

function drag_over_event(event)
{
}
 
var increment, percentage
 
function update_progress()
{              
    percentage = percentage + increment;
	$("#upload_progress_bar").attr('style','width: '+percentage+'%');
	$("#upload_progress_text").text(percentage.toFixed(0)+'%');
	
	if (percentage >=100){
	    setTimeout(function(){
	        $("#upload_progress").fadeOut(400);
	        $("#upload_progress_bar").attr('style','width:0%');
	        $("#upload_progress_text").text('');
	    },3000);
                }
}

function next(file_list, pointer)
{
    if (pointer<=file_list.length)
    {
    	process_file_list(file_list,pointer+1);
    }
}

function process_file_list(file_list,pointer)
{
	
	f = file_list[pointer];
	i= pointer;
	console.log(file_list,f);
	var file_name = f.name;
    
    if (!f.type.match('image.(jpg|jpeg|gif|png)')) {
    
        status_message('danger',
            "Sorry, <b>"+f.name+"</b> is not an image file we can use. JPG, GIF, and PNG are the only filetypes that can be uploaded.",
            'file-upload-error-'+i);

        update_progress();
        next(file_list,pointer);
    }
    
    if (f.size>global.max_filesize){
    
        status_message('danger',
        "Sorry, image <b>"+f.name+"</b> is too large ("+f.size+" bytes). All images must be "+global.max_filesize+" bytes or smaller.",
            'file-upload-error-'+i);

        update_progress();
        next(file_list,pointer);
    }
    
    var fd=new FormData();
    
    fd.append('file-'+i, f);
    fd.append('csrf',global.csrf);
    
    $.ajax({
        type:"POST",
        url:global.base+"/page/"+global.page+"/upload/",
        enctype:"multipart/form-data",
        processData: false,
        contentType: false,
        file: f,
        data: fd,
    }).done(function (data,textStatus,request)
        {
            console.log(request);
            $('#media_list').html(data);
            $('[data-toggle="tooltip"]').tooltip();
            status_message('success',
                "File <b>"+this.file.name+"</b> uploaded successfully.",
                'file-upload-success-'+i);
            	
        }
    ).fail(function(xhr, status, error) {
        reason = xhr.statusText;
        details = $(xhr.responseText).filter('#error_text').html();
        error_report('Sorry, an error occurred when uploading:',details);
    }      
    ).always(function(){
        update_progress();
        next(file_list,pointer);
    });
	
}

function drop_event(event)
{
    event.stopPropagation();
    event.preventDefault();
    
    $(".uploadarea").css('background-color','');
    
    $("#upload_progress").show();
    $("#upload_progress_bar").attr('style','width:0%');
    $("#upload_progress_text").text(''); 
    
    var file_list = event.originalEvent.dataTransfer.files;
    
    increment = 100/file_list.length
    percentage = 0;
    
    process_file_list(file_list,0);
    
    /*
    
    for (var i = 0, f; f = file_list[i]; i++){
        
        var file_name = f.name;
        
        if (!f.type.match('image.(jpg|jpeg|gif|png)')) {
        
            status_message('danger',
                "Sorry, <b>"+f.name+"</b> is not an image file we can use. JPG, GIF, and PNG are the only filetypes that can be uploaded.",
                'file-upload-error-'+i);

            update_progress();
            continue;
        }
        
        if (f.size>global.max_filesize){
        
            status_message('danger',
            "Sorry, image <b>"+f.name+"</b> is too large ("+f.size+" bytes). All images must be "+global.max_filesize+" bytes or smaller.",
                'file-upload-error-'+i);

            update_progress();
            continue;
        }
        
        var fd=new FormData();
        
        fd.append('file-'+i, f);
        fd.append('csrf',global.csrf);
        
	    $.ajax({
	        type:"POST",
	        url:global.base+"/page/"+global.page+"/upload/",
	        enctype:"multipart/form-data",
	        processData: false,
	        contentType: false,
	        file: f,
	        data: fd,
	    }).done(function (data,textStatus,request)
	        {
                console.log(request);
                $('#media_list').html(data);
                $('[data-toggle="tooltip"]').tooltip();
                status_message('success',
                    "File <b>"+this.file.name+"</b> uploaded successfully.",
                    'file-upload-success-'+i);
	        }
	    ).fail(function(xhr, status, error) {
            reason = xhr.statusText;
            details = $(xhr.responseText).filter('#error_text').html();
            error_report('Sorry, an error occurred when uploading:',details);
        }      
	    ).always(function(){
            update_progress();
	    });
	    
    }
    */
    

}
