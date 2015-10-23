<ul class="nav nav-tabs">
% for n in nav_tabs:
% 	if n[0]==nav_default:
% 	  css_class = ' class="active"'
% 	else:
% 	  css_class = ''
% 	end
	<li role="presentation"{{!css_class}}><a href="{{!settings.BASE_URL}}/blog/{{blog.id}}/settings/{{!n[0]}}">{{!n[1]}}</a></li>
% end
</ul>
	
