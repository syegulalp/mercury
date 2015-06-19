function toggle_search()
{
 
    $('#search').toggle();
    if ($('#search').is(':visible'))
    {
        $('#search_text').focus();
    }
}

function clear_search() {
    $('#search_text').val('');
    $('#search_button').click();
}