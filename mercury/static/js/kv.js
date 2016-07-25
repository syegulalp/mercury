function show_activity(target, icon) {
    //$(target).removeClass('glyphicon-*').addClass('glyphicon-'+icon);
    $(target).attr('class', 'glyphicon glyphicon-' + icon)
    $(target).show();
}

function hide_activity(target) {
        $(target).hide();
        $(target).attr('class', '');
    }

function remove_kv(id) {
    var fd = new FormData();
    fd.append('csrf', global.csrf)
    fd.append('kv', id)
    show_activity('#kv_activity', 'remove-sign');
    $.ajax({
        type: "DELETE",
        url: global.base + "/api/1/kv",
        enctype: "multipart/form-data",
        processData: false,
        contentType: false,
        data: fd,
    }).done(function(data, textStatus, request) {
        $('#kv_list').replaceWith($(data).filter('#kv_list'));
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to remove KV: "
        );
    }).always(function() {
        hide_activity('#kv_activity');
    });
}

function add_kv() {
    /*
    var fd = new FormData();
    fd.append('csrf', global.csrf);
    fd.append('kv_new_key_name', $('#kv_new_key_name').val());
    fd.append('kv_new_key_value', $('#kv_new_key_value').val());
    fd.append('kv_object', $('#kv_object').val());
    fd.append('kv_objectid', $('#kv_objectid').val());
    */
    
    show_activity('#kv_activity', 'circle-arrow-up');
    $.post(global.base + "/api/1/kv",
        {'csrf': global.csrf,
        'kv_new_key_name': $('#kv_new_key_name').val(),
        'kv_new_key_value': $('#kv_new_key_value').val(),
        'kv_object': $('#kv_object').val(),
        'kv_objectid': $('#kv_objectid').val()}
        ).done(function(data, textStatus, request) {
        $('#kv_list').replaceWith($(data).filter('#kv_list'));
        $('#kv_new_key_name').val('');
        $('#kv_new_key_value').val('');
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to add KV: ");
    }).always(function() {
        hide_activity('#kv_activity');
    });
}