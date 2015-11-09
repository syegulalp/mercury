% cats = {}
% primary_icon = "<span title='{}' class='glyphicon glyphicon-star'></span>"
% for category in page.categories:
% cats[category.category.id]=category
<p class='category-item'>
% if category.primary==True:
{{!primary_icon.format('Primary category for post')}}
% end
{{category.category.title}} <span title='Remove this category' class='glyphicon glyphicon-remove-sign'></span>
</p>
% end
<hr/>
% for category in page.blog.categories:
% checked = ""
% primary=""
% primary_i = ""
% if category.id in cats:
% 	checked =" checked"
% end
% try:
%	if cats[category.id].primary is True:
%		primary = ' data-primary="Y"'
%	end
% except:
% 	pass
% end
% if category.default is True:
%   primary_i = " "+primary_icon.format('Default category for blog')
% end 
<div class="">
<input name="cat-sel-{{category.id}}" id="cat-sel-{{category.id}}" type="checkbox"{{checked}}{{!primary}}>
<label for="cat-sel-{{category.id}}">{{category.title}}{{!primary_i}}</label>
</div>
% end
