global.background_save_timer = null;
var editor = null;
var editor_resize = function() {}
var editor_update = function() {}
var editor_insert = function() {}
var editor_set_dirty = function() {}
var animation_timeout = null;
var rotate = 0;
var colors = [
    ['#000', '#f00'],
    ['#fff', '#f00']
];

function calc_size() {
    ht = 0;
    $('.resize,.footer').each(function() {
        ht += $(this).height();
        ht += parseInt($(this).css('margin-bottom'), 10);
        ht += parseInt($(this).css('margin-top'), 10);
    });
    ht += parseInt($('#editor_div').css('margin-bottom'), 10);
    return ht;
}

function set_background_save_timer(){
    global.background_save_timer=window.setTimeout(
        function(){
            background_save_draft();
        }, 1000
    );
    console.log('Timer triggered');
}

function clear_background_save_timer(){
    window.clearTimeout(global.background_save_timer);
}

function background_save_draft(){
    console.log('Backup triggered');
    backup = JSON.stringify($('#main_form').serializeArray());
    localStorage.setItem('backup-'+global.page,backup);
}

function leave() {}

function stay() {
    return "You may have unsaved changes on this page.";
}

function delayed_resize() {
    try {
        editor_resize();
    } catch (err) {
        setTimeout(function() {
            delayed_resize()
        }, 50);
    }
}


function save_animation(n) {
    n.css('color', colors[rotate][0])
    n.css('text-shadow', '0 0 4px ' + colors[rotate][1])
    rotate = 1 - rotate;
    animation_timeout = setTimeout(function() {
        save_animation(n)
    }, 333);
}

function reset_animation(n) {
    n.css('color', '#ffffff');
    n.css('text-shadow', '');
    clearTimeout(animation_timeout);
}

function delete_media(media_id) {
    var fd = new FormData();
    fd.append('csrf', global.csrf);
    $.ajax({
        type: "POST",
        url: global.base + "/page/" + global.page + "/media/" +
            media_id + "/delete",
        enctype: "multipart/form-data",
        processData: false,
        contentType: false,
        data: fd,
    }).done(function(data, textStatus, request) {
        $('#media_list').html(data);
        status_message('success', 'Media ID#' + media_id +
            ' successfully removed from page.',
            'delete-success-' + media_id);
        window.onbeforeunload = stay;
    });
}

function add_template(template_id, media_id) {
    form = $('#img_template');
    form_array = $(form).serializeArray();
    template_id = form_array[0].value;
    media_id = form_array[1].value;
    url = global.base + "/page/" + global.page + "/add-media/" + media_id +
        "/" + template_id;
    $.get(url).done(function(data) {
        editor_insert(data);
        $('#modal_close_button').click();
    });
}


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



function bind_queue() {
    $('#show_queue').bind('click', function() {});
}

function run_queue(blog_id) {
    $.get(global.base + "/blog/" + global.blog + "/publish/process").done(
        function(data) {
            $('#queue_counter').replaceWith(data);
            result = parseInt($('#queue_counter_num').attr('data-count'));
            if (result > 0) {
                run_queue(blog_id);
            }
        }).fail(function(xhr, status, error) {
        reason = xhr.statusText;
        details = $(xhr.responseText).filter('#error_text').html();
        error_report(
            'Sorry, an error occurred in the publishing queue:',
            details);
    });;
}

function page_save(n) {
    if (global.saving == true) return;
    clear_background_save_timer();
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
    return (
        '<span id="response_icon">&nbsp;<span class="glyphicon glyphicon-' +
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
    $('.tag-title').each(function() {
        tag_id = $(this).data('tag');
        if (tag_id != 0) {
            tags.push(tag_id);
        } else {
            new_tags.push($(this).data('new-tag'));
        }
    });
    $('#tag_text').attr('value', JSON.stringify(tags));
    $('#new_tags').attr('value', JSON.stringify(new_tags));
    $('#save_animation').html(icon('refresh'));
    save_animation($('#save_animation'));
    global.saving = true;
    global.original_title = document.title;
    document.title = "[Saving] " + document.title;
    $.post('', form.serialize()).done(function(data, textStatus, xhr) {
        window.onbeforeunload = leave;
        if (xhr.getResponseHeader('X-Redirect')) {
            window.location = xhr.getResponseHeader('X-Redirect');
            return 0;
        }
        $('#messages_float').empty();
        $('#messages_float').append($(data).filter('#messages'));
        $('#sidebar_inner').empty();
        $('#sidebar_inner').replaceWith($(data).filter(
            '#sidebar_inner'));
        $('#queue_counter').empty();
        $('#queue_counter').append($(data).filter('#queue_counter'));
        $('title').empty();
        $('title').append($(data).filter('title').html());
        sidebar_wireup();
        $('#save_animation').html(icon('ok-sign'));
        localStorage.removeItem('backup-'+global.page);
        dismiss('#alert_message', 2500);
        dismiss('#response_icon', 2500);
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to save: ");
        $('#save_animation').html(icon('remove-sign'));
    }).always(function() {
        global.saving = false;
        reset_animation($('#save_animation'));
        document.title = global.original_title;
        $('#backup').val('N');
    });
}

function template_save(action) {
    console.log(action);
    editor_update();
    $('#save').attr('value', action);
    form = $('#main_form');
    $('#save_animation').html(icon('refresh'));
    save_animation($('#save_animation'));
    $.post('', form.serialize()).done(function(data, textStatus, xhr) {
        window.onbeforeunload = leave;
        if (xhr.getResponseHeader('X-Redirect')) {
            window.location = xhr.getResponseHeader('X-Redirect');
            return 0;
        }
        $('#messages_float').empty();
        $('#messages_float').append($(data).filter('#messages'));
        $('#sidebar_inner').empty();
        $('#sidebar_inner').replaceWith($(data).filter(
            '#sidebar_inner'));
        $('#queue_counter').empty();
        $('#queue_counter').append($(data).filter('#queue_counter'));
        $('title').empty();
        $('title').append($(data).filter('title').html());
        sidebar_wireup();
        $('#save_animation').html(icon('ok-sign'));
        dismiss('#alert_message', 2500);
        dismiss('#response_icon', 2500);
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to save: ");
        $('#save_animation').html(icon('remove-sign'));
    }).always(function() {
        reset_animation($('#save_animation'));
    });
}

function sidebar_wireup() {
    if ('template_body' in window) {
        $('#preview').on('click', function() {
            window.open(global.base + "/template/" + global.template +
                "/preview", "preview_" + global.template);
        });
    } else {
        $("#revision_link").on("click", function() {
            open_modal(global.base + "/page/" + global.page +
                "/edit/revisions");
        });
        $("#insert_media_link").on("click", function() {
            open_modal(global.base + "/page/" + global.page +
                "/media/add");
        });
        if ($('#publication_date_picker').datetimepicker != undefined) {
            $('#publication_date_picker').datetimepicker({
                format: 'YYYY-MM-DD HH:mm:ss',
                showTodayButton: true
            });
        }
        $(".uploadarea").on("dragover", drag_enter_event);
        $(".uploadarea").on("dragleave", drag_leave_event);
        $(".uploadarea").on("drop", drop_event);
        
        init_typeahead('tags');
        
        $('.typeahead').bind('typeahead:select', function(ev, suggestion) {});
        $('.typeahead').on('keypress', function(event) {
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
    $('[data-toggle="tooltip"]').tooltip({
        html: true
    })
    $('.unsaved').on("input", function() {
        window.onbeforeunload = stay;
    });
    $(document).off("keypress", ".entersubmit");
    $(document).on("keypress", ".entersubmit", function(event) {
        var keyCode = event.which || event.keyCode;
        if (keyCode == 13) {
            // event.stopPropagation();
            event.preventDefault();
            $("#save_button").trigger('click');
            return false;
        } else {
            return true;
        }
    });
}

function activate_tags() {
    $('.tag-remove').on('click', function(event) {
        remove_tag(event, this);
    });
}

function remove_tag(e, t) {
    $(t).parent().remove();
    editor_set_dirty();
}

function add_tag(e) {
    tag = e.value;
    if (tag.length < 1) {
        return false;
    }
    var no_match = true;
    $('.tag_link').each(function() {
        if (e.value == $(this).text()) {
            $(this).parent().parent().fadeIn(200).fadeOut(200).fadeIn(
                200).fadeOut(200).fadeIn(200);
            no_match = false;
            return false;
        }
    });
    if (no_match == false) {
        return false;
    }
    $('.typeahead').typeahead('val', '');
    $('.typeahead').typeahead('close');
    var fd = new FormData();
    fd.append('csrf', global.csrf);
    fd.append('tag', tag)
    if (global.page == "None") {
        url_link = "blog/" + global.blog;
    } else {
        url_link = "page/" + global.page;
    }
    $('#tag_activity').removeClass('glyphicon-refresh').addClass(
        'glyphicon-circle-arrow-up');
    $('#tag_activity').show();
    $.ajax({
        type: "POST",
        url: global.base + "/api/1/make-tag-for-page/" + url_link,
        enctype: "multipart/form-data",
        processData: false,
        contentType: false,
        data: fd,
    }).done(function(data, textStatus, request) {
        $('#tag_list').append($(data));
        activate_tags();
        editor_set_dirty();
    }).fail(function(xhr, status, error) {
        server_failure(xhr, status, error,
            "Sorry, an error occurred when trying to add tag: "
        );
    }).always(function() {
        $('#tag_activity').hide();
        $('#tag_activity').removeClass('glyphicon-circle-arrow-up')
            .addClass('glyphicon-refresh');
    });
}

function show_local_preview() {
    window.open(global.base + "/page/" + global.page + "/preview",
        "preview_" + global.page);
}


    //circle-arrow-up
    //refresh



$(window).load(function() {
    // conditional binding of editor
    // this changes depending on what editor we're using
    // might need to find more elegant ways to do it to make it
    // plugin-friendly
    // e.g., iterate through a list of possible object names and
    // then run the
    // function hooked to that
    if ('page_text' in window) {
        editor = tinymce;
        editor_update = function() {
            tinymce.triggerSave();
        }
        editor_resize = function() {
            if ($('.mce-fullscreen').length != 0) {
                return
            }
            e = tinymce.activeEditor;
            var targetHeight = window.innerHeight - $("#editor_div")
                .offset().top;
            var mce_bars_height = 0;
            $('.mce-toolbar, .mce-statusbar, .mce-menubar').each(
                function() {
                    mce_bars_height += $(this).height();
                });
            var myHeight = targetHeight - mce_bars_height - $(
                '#page_text_label').height();
            e.theme.resizeTo(null, myHeight);
        }
        editor_insert = function(text) {
            tinymce.activeEditor.execCommand('mceInsertContent',
                false, text);
        }
        editor_set_dirty = function() {
            set_background_save_timer();
            window.onbeforeunload = stay;            
        }
        tinymce.init(global.html_editor_settings);

    }
    if ('template_body' in window) {
        editor = myCodeMirror;
        editor_resize = function() {
            $('.CodeMirror').css('height', (window.innerHeight - $(
                ".CodeMirror").offset().top - calc_size()));
            editor.refresh();
        }
        editor_update = function() {
            editor.save();
            editor.refresh();
        }
        setTimeout(function() {
            delayed_resize()
        }, 50)
    }
    if (editor != null) {
        $(window).bind("resize", function() {
            editor_resize();
        });
        if ('page_text' in window) {
            var observer = new MutationObserver(function(mutations,
                observer) {
                setTimeout(function() {
                    delayed_resize();
                }, 50);
            });
            observer.observe(document.querySelector('#editor_div'), {
                childList: true,
                subtree: true
            });
        }
        window.onbeforeunload = leave;
        sidebar_wireup();
        $('#page_title').focus();
    }
});