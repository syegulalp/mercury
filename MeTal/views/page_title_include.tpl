% if page:
<title>{{page.title}} - {{blog.name}} | {{settings.PRODUCT_NAME}}</title>
% elif blog:
<title>{{blog.name}} | {{settings.PRODUCT_NAME}}</title>
% elif site:
<title>{{site.name}} | {{settings.PRODUCT_NAME}}</title>
% else:
<title>{{settings.PRODUCT_NAME}}</title>
% end