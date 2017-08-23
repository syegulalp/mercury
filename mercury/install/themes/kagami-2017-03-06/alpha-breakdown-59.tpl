<!--

- Need to paginate the results in alpha boundaries? not sure we need this
- Also need some way to ensure any rebuilds from a template are confined to the page in question

Main problem we have is that any regeneration of a given alpha across multiple pages
must also regenerate others because of overflow, etc.
At least this way we're regenerating only the alphas that matter.
therefore, a tag with 'a' will just regenerate all 'a' pages

function: return /a/<page #> for each pagination in the total number of items in that alpha

-->

<%
   letters = [chr(n) for n in range(97,97+36)]+[chr(n) for n in range(48,59)]
   
   from core.models import Tag
   obj='anime'
   l = len(obj)+2
   for m in letters:
   taglist = blog.tags.where(Tag.tag.startswith(obj+': '+m)).order_by(Tag.tag.asc())
   if taglist.count()>0:
%>
  <h3>{{m.upper()}}</h3>
% if taglist.count()>1:  
% t=[taglist[0],taglist[taglist.count()-1]]
  <p>{{t[0].tag[l:]}} ... {{t[1].tag[l:]}}</p> 
% elif taglist.count()>0:
  <p>{{taglist[0].tag[l:]}}</p>
% end
% end  
% end  
   