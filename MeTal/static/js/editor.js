var editor = null;
var editor_resize = function(){}
var editor_update = function(){}
var editor_insert = function(){}
var editor_set_dirty = function(){}

var rotate_timeout = null;
var rotate = 0;

function leave(){}

function stay(){
    return "You may have unsaved changes on this page.";
}

function delayed_resize(){
    try
    {
        editor_resize();
    }
    catch(err)
	{
	   setTimeout(function(){delayed_resize()},50);
	}
	
}

function save_animation(n){
    rotate = rotate+ 15;
    n.css('transform','rotate(' + rotate + 'deg)');
    rotate_timeout = setTimeout(function(){save_animation(n)},100);
}

function reset_animation(n){
    rotate = 0;
    clearTimeout(rotate_timeout);
    n.css('transform','');    
}


function delete_media(media_id){

    var fd=new FormData();
    fd.append('csrf',global.csrf);

    $.ajax({
        type:"POST",
        url:global.base+"/page/"+global.page+"/media/"+media_id+"/delete",
        enctype:"multipart/form-data",
        processData: false,
        contentType: false,
        data: fd,
    }).done(function (data,textStatus,request)
        {
            $('#media_list').html(data);
            status_message('success','Media ID#'+media_id+' successfully removed from page.',
        'delete-success-'+media_id);
            window.onbeforeunload = stay;
        
        }
    ); 
}

function add_template(template_id, media_id){
    
    form = $('#img_template');
    form_array = $(form).serializeArray();
    console.log(form_array);
    template_id = form_array[0].value;
    media_id = form_array[1].value;
    
    url= global.base+"/page/"+global.page+"/add-media/"+media_id+"/"+template_id;
    
    $.get(url).done(function(data){
    
        editor_insert(data);
        $('#modal_close_button').click();
    
    });   
     
}

function open_modal(url) {
    $.get(url)
        .done(function(data) {

            $('#modal_container').empty();
            $('#modal_container').append($(data));
            $('#modal_contents').modal();

        });
}

function status_message(type,string,id){

    $('#messages_float').append(
        '<div id="messages-inner" class="col-xs-12">'+
        '<div id="'+id+'" class="alert alert-'+type+'" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
        '<span class="glyphicon glyphicon-warning-sign"></span>&nbsp;' +
        string +
        '</div></div>');

    if (type!="danger"){
        dismiss('#'+id, 2500);
    }
}

function error_report(header,reason){
    status_message('danger',header+reason,'server-error')
}

function bind_queue() {
    $('#show_queue').bind('click', function() {});
}

function run_queue(blog_id) {

    $.get(global.base + "/blog/" + global.blog +
            "/publish/process")
        .done(function(data) {

            $('#queue_counter').replaceWith(data);

            result = parseInt($('#queue_counter_num').attr(
                'data-count'));

            if (result > 0) {
                run_queue(blog_id);
            }

        }).fail(function(xhr, status, error) {
            reason = xhr.statusText;
            details = $(xhr.responseText).filter('#error_text').html();
            error_report('Sorry, an error occurred in the publishing queue:',details);           

        });;

}

function page_save(n) {
    $('#save').attr('value', n);
    editor_update();
    editor_resize(tinymce.activeEditor);
    form_save($('#main_form'));    
}

function dismiss(object, timeout) {

    setTimeout(function() {
        $(object).fadeOut(function() {
            $(object).remove()
        });

    }, timeout);

}

function icon(type) {
    
    return ('<span id="response_icon">&nbsp;<span class="glyphicon glyphicon-' +
        type + '"></span></span>');
}


function form_save(form) {

    if ($('#save').attr('value') == 4) {
        if (confirm(
                "You are about to close this page without saving any changes. Is this OK?"
            )) {
            window.location = global.base + "/blog/" + global.blog;
        }

        return 0;
    }

    if ($('#save').attr('value') == 16) {
        if (!confirm(
                "You are about to delete this page. This action cannot be undone. Is this OK?"
            )) {
            return 0;
        }

    }
    
    tags = []
    new_tags = []
    
    $('.tag-title').each(function(){
        tag_id = $(this).data('tag');
        if (tag_id!=0){tags.push(tag_id);}
        else {new_tags.push($(this).data('new-tag'));}
    });
    
    $('#tag_text').attr('value',JSON.stringify(tags));
    $('#new_tags').attr('value',JSON.stringify(new_tags));
    
    $('#save_animation').html(icon('refresh'));
    
    save_animation($('#save_animation'));

    $.post('', form.serialize())
        .done(function(data, textStatus, xhr) {
        
            window.onbeforeunload = leave;

            if (xhr.getResponseHeader('X-Redirect')) {
                window.location = xhr.getResponseHeader(
                    'X-Redirect');
                return 0;
            }

            $('#messages_float').empty();
            $('#messages_float').append($(data).filter(
                '#messages'));

            $('#sidebar_inner').empty();
            $('#sidebar_inner').replaceWith($(data).filter(
                '#sidebar_inner'));

            $('#queue_counter').empty();
            $('#queue_counter').append($(data).filter(
                '#queue_counter'));

            $('title').empty();
            $('title').append($(data).filter('title').html());

            sidebar_wireup();

            $('#save_animation').html(icon('ok-sign'));

            dismiss('#alert_message', 2500);
            dismiss('#response_icon', 2500);


        })
        .fail(function(xhr, status, error) {

            if (xhr.readyState == 0)
            {
                reason = "Couldn't reach the server.";
                details= "";
            }
            else
            {
                reason = xhr.statusText;
                details = $(xhr.responseText).filter('#error_text').html();
            }
            
            error_report("Sorry, an error occurred when trying to save: ",reason+details);
            

            $('#save_animation').html(icon('remove-sign'));

        }).always(function() {
            reset_animation($('#save_animation'));
        });
}

function sidebar_wireup() {

    // FIXME: This function isn't properly written for non-page editor sidebars

    $('[data-toggle="tooltip"]').tooltip({
        html: true
    })

    $("#revision_link").on("click", function() {
        open_modal(global.base + "/page/" + global.page +
            "/edit/revisions");
    });
    
    if ($('#publication_date_picker').datetimepicker != undefined)
    {
	    $('#publication_date_picker').datetimepicker({
	        format: 'YYYY-MM-DD HH:mm:ss',
	        showTodayButton: true
	        });
    }
    
    $('.unsaved').on("input", function() {
        window.onbeforeunload = stay;
    });
    
    $(document).off("keypress", ".entersubmit");

    $(document).on("keypress", ".entersubmit", function(event) {
        var keyCode = event.which || event.keyCode;
        
        if (keyCode == 13) {
            //event.stopPropagation();
            event.preventDefault();
            $("#save_button").trigger('click');
            return false;
        } else {
            return true;
        }
    });
    
    $(".uploadarea").on("dragover",drag_enter_event);
    $(".uploadarea").on("dragleave",drag_leave_event);
    $(".uploadarea").on("drop",drop_event);
    
    init_typeahead('tags');
    
    $('.typeahead').bind('typeahead:select', function(ev, suggestion) {
        console.log('Selection: ' + suggestion);        
    });
    
    $('.typeahead').on('keypress',function(event) {
        var keyCode = event.which || event.keyCode;
        
        if (keyCode == 13) {
            event.preventDefault();
            add_tag(this);
            return false;
        } else {
            return true;
        }
    });
    
    activate_tags();    
    
}


function activate_tags(){

    $('.tag-remove').on('click',function(event){
        remove_tag(event,this);
    });
}

function remove_tag(e,t){
    $(t).parent().remove();
    editor_set_dirty();      
}


function add_tag(e){

    tag = e.value;
    
    var no_match = true;
    
    $('.tag_link').each(function(){
        console.log($(this).text());
        if (e.value == $(this).text())
        {
            $(this).parent().parent().fadeIn(200).fadeOut(200).fadeIn(200).fadeOut(200).fadeIn(200);
            no_match = false;
            return false;
        }
    }); 
    
    if (no_match==false) { return false;}       
    
    $('.typeahead').typeahead('val', '');
    $('.typeahead').typeahead('close');
    
    var fd=new FormData();
    fd.append('csrf',global.csrf);
    fd.append('tag',tag)
    
    if (global.page == "None")
    { url_link = "blog/"+global.blog}
    else
    { url_link = "page/"+global.page}
    
    $.ajax({
        type:"POST",
        url:global.base+"/api/1/make-tag-for-page/"+url_link,
        enctype:"multipart/form-data",
        processData: false,
        contentType: false,
        data: fd,
    }).done(function (data,textStatus,request)
        {
            $('#tag_list').append($(data));
            activate_tags();
            editor_set_dirty();
        }
    ); 
 
}


function show_local_preview(){
    window.open(global.base+"/page/"+global.page+"/preview","preview_"+global.page);
}



$(window).load(function() {

    // conditional binding of editor
    // this changes depending on what editor we're using
    // might need to find more elegant ways to do it to make it plugin-friendly
    // e.g., iterate through a list of possible object names and then run the 
    // function hooked to that
    
    if ('page_text' in window)
    {
	    editor = tinymce;
	    
	    editor_update = function(){tinymce.triggerSave();}
	    editor_resize = function(){
	        
	        if ($('.mce-fullscreen').length != 0){return}
             
            e = tinymce.activeEditor;                  	        
	        
	        var targetHeight = window.innerHeight - $("#editor_div").offset().top;
	        var mce_bars_height = 0;
	        $('.mce-toolbar, .mce-statusbar, .mce-menubar').each(function(){
	                mce_bars_height += $(this).height();
	        });
	        var myHeight = targetHeight - mce_bars_height - $('#page_text_label').height();        
	 
	        e.theme.resizeTo(null,myHeight);
            
	    }
	    
	    editor_insert = function(text){
            tinymce.activeEditor.execCommand('mceInsertContent', false, text);
        }
        
        editor_set_dirty = function(){
            window.onbeforeunload = stay;
        }
        	    
	    tinymce.init({
	        init_instance_callback: function(){
	           
            },
		    setup: function (ed) {
		        ed.on('init', function(args) {
		            window.onbeforeunload = leave;		            
		        });
                ed.on('change',function() {
                    window.onbeforeunload = stay;            
                });
            },            
	        selector: "textarea.editor",
	        entity_encoding: "named",
	        browser_spellcheck: true,
	        cleanup_on_startup: true, 
	        content_css: global.base + '/blog/'+global.blog+'/editor-css',
	        plugins: [
	                "advlist save autosave link image lists hr anchor pagebreak",
	                "searchreplace wordcount visualblocks visualchars code fullscreen media nonbreaking",
	                "table contextmenu template textcolor paste colorpicker textpattern"
	        ],
            style_formats: [
		        {title: 'Standard graf', block: 'p'},
		        {title: 'Head', block: 'p', classes: 'lead'},
		        {title: 'Small', block: 'small'},
		    ],
	        toolbar1: "save | styleselect formatselect | bold italic underline strikethrough removeformat | bullist numlist | outdent indent blockquote hr | link unlink anchor image | visualchars visualblocks nonbreaking template pagebreak | code fullscreen",
	
	        save_enablewhendirty: true,
	        save_onsavecallback: function() {$("#save_button").click();},
	        menubar: false,
	        toolbar_items_size: 'small',
	
	        templates: [
	                {title: 'Test template 1', content: 'Test 1'},
	                {title: 'Test template 2', content: 'Test 2'}
	        ]
	        });

    }
    
    if ('template_body' in window)

    {
    
        editor = 1

        editor_resize = function() {
            $('.CodeMirror').css('height', (
                window.innerHeight - $(".CodeMirror").offset().top - 
                ($(".footer").height() * 5)
            ));
        }
    }
    
    
    if (editor != null)
    {
        
        $(window).bind("resize", function() {
            editor_resize();
        });
        
        var observer = new MutationObserver(function(mutations, observer) {
            setTimeout(function(){delayed_resize()},50);
        });
         
        observer.observe(document.querySelector('#editor_div'),
            {childList:true, subtree:true});   

        
        if ($('#alert_message').length) {
            dismiss('#alert_message', 2500);
        }
        
        window.onbeforeunload = leave;
    
        sidebar_wireup();
        
        $('#page_title').focus();
        
    }
    
});