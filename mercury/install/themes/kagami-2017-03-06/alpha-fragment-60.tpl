% obj = fileinfo.file_path.split('/')[0]
<h1>{{obj}}</h1><hr/>
% from core.models import Tag
% for n in blog.tags.where(Tag.tag.startswith(obj+': ')).order_by(Tag.tag).naive():
    <h3><a href="{{utils.create_basename_core(n.tag.split(': ')[1])}}">{{n.tag[len(obj)+2:]}}</a></h3>
% end    