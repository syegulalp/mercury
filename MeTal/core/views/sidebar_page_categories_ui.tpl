% for category in page.categories:
<p>
% if category.primary==True:
*
% end
{{category.category.title}}
% end