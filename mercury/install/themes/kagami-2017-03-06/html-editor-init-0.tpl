{
    init_instance_callback: function() {

    },
    setup: function(ed) {
        ed.on('init', function(args) {
            window.onbeforeunload = leave;
        });
        ed.on('change', function() {
            window.onbeforeunload = stay;
        });
    },
    selector: "textarea.editor",
    convert_urls: false,
    entity_encoding: "named",
    browser_spellcheck: true,
    cleanup_on_startup: true,
    content_css: global.base + '/blog/' + global.blog + '/editor-css',
    plugins: [
        "advlist save autosave link image lists hr anchor pagebreak",
        "searchreplace wordcount visualblocks visualchars code fullscreen media nonbreaking",
        "table contextmenu template textcolor paste colorpicker textpattern"
    ],
    style_formats: [{
        title: 'Standard graf',
        block: 'p'
    }, {
        title: 'Head',
        block: 'p',
        classes: 'lead'
    }, {
        title: 'Small',
        block: 'small'
    }, {
        title: 'Code',
        inline: 'code'
    }, {
        title: 'Alert',
		block: 'div',
        classes: 'alert alert-info'
    }, ],
    toolbar1: "save | styleselect formatselect | bold italic underline strikethrough removeformat | bullist numlist | outdent indent blockquote hr | link unlink anchor image | visualchars visualblocks nonbreaking template pagebreak | code fullscreen",

    save_enablewhendirty: true,
    save_onsavecallback: function() {
        $("#save_button").click();
    },
    menubar: false,
    toolbar_items_size: 'small',

    templates: [{
        title: 'Test template 1',
        content: 'Test 1'
    }, {
        title: 'Test template 2',
        content: 'Test 2'
    }]
}