editor_css = '''
body, td, pre {color:#000; font-family: serif;
    font-size:16px;}

body {
    max-width: 600px;
    margin: auto;
    padding: 12px;
    border-left: 1px #eeeeee solid;
    border-right: 1px #eeeeee solid;
    border-bottom: 1px #eeeeee solid;
    font-family: 'Calibri', sans-serif;
    font-size: 15px;
    line-height: 125%;
}

img {
    max-width:100%;
}

div.screenshot
{
    background-color: #f0f0f0;
    text-align:center;
}

div.screenshot.screenshot-double img
{
    max-width:49%;
}

.lead{
    font-weight:bold;
}

.more {
    border-top: 1px #a0a0a0 dashed;
}

.screenshot img{
    width: 48%;
}
'''

codemirror_css = '''
.CodeMirror {
    height: auto;
}
'''

html_editor_settings = '''
{
    init_instance_callback: function() {

    },
    setup: function(ed) {
        console.log('Hello');
        ed.on('init', function(args) {
            window.onbeforeunload = leave;
        });
        ed.on('change', function(e) {
            editor_set_dirty();
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
'''
