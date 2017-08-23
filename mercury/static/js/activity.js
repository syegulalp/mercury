function dismiss(object, timeout) {
    setTimeout(function() {
        $(object).fadeOut(function() {
            $(object).remove();
        });
    }, timeout);
}

function adjust_error_view() {
    pos1 = $('#error_header').innerHeight();
    try
    {
        pos2 = $('#error_scrollable').offset().top;
        $('#error_scrollable').css('overflow-y', 'scroll');
        $('#error_scrollable').height(window.innerHeight - pos1 - pos2 - 32);
    }
    catch (e) {
        if (e instanceof TypeError) {}
        else {throw e;}
    }
}


function status_message(type, string, id, sign='warning-sign') {
    $('#messages_float').append(
        '<div id="messages-inner" class="col-xs-12">' + '<div id="' +
        id + '" class="alert alert-' + type + '" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
        '<span class="glyphicon glyphicon-'+sign+'"></span>&nbsp;' +
        string + '</div></div>');
    if (type != "danger") {
        dismiss('#' + id, 2500);
    }
}

function error_report(header, reason) {
    status_message('danger', header + reason, 'server-error');
    adjust_error_view();
}

function server_failure(xhr, status, error, sorry_message) {
    if (xhr.readyState === 0) {
        reason = "Couldn't reach the server.";
        details = "";
    } else {
        reason = xhr.statusText;
        details = $(xhr.responseText).filter('#error_text').html();
    }
    error_report(sorry_message, reason + details);
}


function show_activity(target, icon) {
    //$(target).removeClass('glyphicon-*').addClass('glyphicon-'+icon);
    $(target).attr('class', 'glyphicon glyphicon-' + icon)
    $(target).show();
}

function hide_activity(target) {
        $(target).hide();
        $(target).attr('class', '');
    }