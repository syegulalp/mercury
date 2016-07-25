% if page:
% if page.id is None:
<title>[New page] - {{blog.name}} | {{settings.PRODUCT_NAME}}</title>
% else:
<title>{{page.title}} - {{blog.name}} | {{settings.PRODUCT_NAME}}</title>
% end
% elif blog:
<title>{{blog.name}} | {{settings.PRODUCT_NAME}}</title>
% elif site:
<title>{{site.name}} | {{settings.PRODUCT_NAME}}</title>
% else:
<title>{{settings.PRODUCT_NAME}}</title>
% end