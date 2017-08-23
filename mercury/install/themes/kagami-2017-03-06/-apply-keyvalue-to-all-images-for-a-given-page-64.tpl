% page_id = 1571
% _key = 'copyright'
% _value = "© Hiroya Oku · Shueisha · \"GANTZ:O\" Production Committee"
% # ----------------------------------------
% from core.models import *
% page = Page.load(page_id)
{{!page.title}}
% for n in page.media:
<p>{{!n.id}}
% if n.kv_val(_key)is not None:
% for m in n.kv_list():
<p>{{!m.id}}/{{!m.key}}/{{!m.value}}
% end  
% else:
<p>None found, setting: {{!n.kv_set(_key,_value)}}  
% end
% end