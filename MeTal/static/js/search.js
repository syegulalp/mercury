function toggle_search()
{
 
    $('#search').toggle();
    if ($('#search').is(':visible'))
    {
        $('#search_text').focus();
    }
}

function clear_search() {
    if ($('#search_text').val().length>0) 
    {$('#search_text').val('');}
    else    
    {$('#search_button').click();}
}