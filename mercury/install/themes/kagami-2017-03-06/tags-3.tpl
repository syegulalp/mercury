%colors={'anime':'success','demographic':'info','meta':'primary','people':'danger'}
% for n in page.tags_public:
% tag_p = n.tag.split(': ',1)
% tag_url = utils.create_basename_core(tag_p[1])
<a href="/{{tag_p[0]}}/{{tag_url}}"><span class="label label-{{!colors[tag_p[0]]}}">{{!n.tag}}</span></a>&nbsp;
% end