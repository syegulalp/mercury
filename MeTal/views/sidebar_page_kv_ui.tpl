% try:
% keys = page.kvs(None,(1,))
% except:
% keys = []
% for n in keys:
<p>{{n.key}}: {{n.value}}
% end
% end