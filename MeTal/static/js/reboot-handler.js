function reboot_stage_1()
{
    //var fd = new FormData();
    //fd.append('csrf', global.csrf);
    //fd.append('csrf', $('#nonce').val());
    // why not just put this stuff into a form already on the page?
    var fd=$('#form');
    
    $.ajax({
        type : "POST",
        url : global.base + "/system/reboot/",
        enctype : "multipart/form-data",
        processData : false,
        contentType : false,
        data : fd,
    }).done(function(data, textStatus, request) {
        
    }()).fail();
}