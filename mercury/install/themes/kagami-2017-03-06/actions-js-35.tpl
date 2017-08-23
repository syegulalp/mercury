function hidemenu(){
  /* $("#newarticles").collapse('hide'); */
}

function no_cookie(id){
    
	var date = new Date();
    days = 30;
    date.setTime(+ date + (days * 86400000));
	document.cookie = 'no-'+id+'=yes;path=/;expires='+ date.toGMTString();

}

window.onload = function()
{

	global = {};
	global.menu = false;

	$("img.lazy").lazyload({
		effect: "fadeIn",
		skip_invisible: false,
		failure_limit: 128
	});

	$(document).delegate('*[data-toggle="lightbox"]', 'click', function(event) {
		event.preventDefault();
		$(this).ekkoLightbox();
	});

	$(".even").each(function() {
        window.requestAnimationFrame(function(){

		words_min = $(this).data('even') || 3;

		var wordArray = $(this).text().split(" ");

		if (wordArray.length > words_min) {


			ks = "";
			for (n = 0; n < words_min; n++) {
				wa = wordArray[wordArray.length - words_min + n];


				if (n < words_min - 1) {
					sep = "&nbsp;";
					if (wa.length > 7) {
						sep = " ";
					}
				} else {
					sep = "&nbsp;";
				}
				if (n == 0) {
					sep = "";
				}
				ks += (sep + wa);
			}
			for (n = 0; n < words_min; n++) {
				wordArray.pop();
			}
			wordArray[wordArray.length] = ks;

			$(this).html(wordArray.join(" "));
		}
        });
	});

	if (document.cookie.indexOf("no-patreon") >= 0) {
		$("#patreon-alert").hide();
	}
	else {
		xx = setTimeout(function(){$("#patreon-alert").fadeIn();},1000);
	}

	if (document.cookie.indexOf("no-comment-alert") >= 0) {
		$("#comment-alert").hide();
	}

	$('.carousel').carousel({
  		interval: 5000
	});

	$('.tooltip-social').tooltip({
  		selector: "a[data-toggle=tooltip]"
	});

}