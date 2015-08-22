% #try:
% #queue_count = queue.count()
% #queue_count = queue_count
% #except:
% #pass
% #end
<span id="queue_counter">
  % if queue_count>0:
<span id="queue_counter_num" data-count="{{queue_count}}" class="label label-danger">{{queue_count}}</span>
  % else:
<span  id="queue_counter_num" data-count="{{queue_count}}" style="color:#4cae4c" class="glyphicon glyphicon-ok-sign"></span>
  % end
</span>