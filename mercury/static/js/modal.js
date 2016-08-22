
function open_modal(url) {
    $('#modal').modal();
    $('#modal_content').empty().append(
        '<div class="modal-body"><p>Loading... </p></div>');
    $.get(url).done(function(data) {
        $('#modal_content').empty().append($(data));
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to load the list of page revisions: "
        );
    });
}
