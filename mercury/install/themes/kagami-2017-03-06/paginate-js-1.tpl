function get_article_preview(a) {
    var b = "/new/" + a + ".txt";
    return $.get(b, function() {})
}

function go(a) {
    get_article_preview(a).always(function(a) {
        loop_it(a)
    })
}

function loop_it(a) {
    var b = $(a).get(0);
    if (-1 == direction) var c = $(b).attr("data-next"),
        d = $(b).attr("data-previous"),
        e = $("#previouslink"),
        f = $("#nextlink");
    else var c = $(b).attr("data-previous"),
        d = $(b).attr("data-next"),
        f = $("#previouslink"),
        e = $("#nextlink");
    var g = c;
    if (b || (b = ""), $("#article-preview-" + String(stub)).html(b), stub == first_counter) {
        var h = "";
        d && (h = "get_articles(" + d + "," + String(-direction) + ")"), e.attr("onclick", h)
    }
    if (stub != last_counter) return stub += direction, go(c);
    var i = "";
    g && (i = "get_articles(" + g + "," + String(direction) + ")"), f.attr("onclick", i)
}

function get_articles(a, b) {
    direction = b, -1 == direction ? (stub = 3, first_counter = 3, last_counter = 1, direction_data = "data-previous") : (stub = 1, first_counter = 1, last_counter = 3, direction_data = "data-next"), go(a)
}


var stub = 0,
    counter = 0,
    left_counter = 0,
    right_counter = 0,
    direction_data = "",
    direction = 0,
    to_append;