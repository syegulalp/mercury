<li class="dropdown" id="queue_counter">
<a href="#" title="Publishing queue status" id="queue_status" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">
% if queue_count>0:
<span id="queue_counter_num" data-count="{{queue_count}}" class="label label-danger">{{queue_count}}</span>
% else:
<span id="queue_counter_num" data-count="{{queue_count}}" style="color:#4cae4c" class="glyphicon glyphicon-ok-sign"></span>
% end
<span class="visible-xs-inline">&nbsp;Queue</span>
</a>
          
<ul class="dropdown-menu" role="menu">
  
    <li role="presentation" class="dropdown-header" >Publishing queue</li>
    
    % if blog is not None:
    % if queue_count>0: #if queue.count():
    <li><a target="_blank" href="{{settings.BASE_URL}}/blog/{{blog.id}}/publish">Publish items in queue</a></li>
    <li class="divider"></li>
    % else:
    <li class="disabled"><a href="#">Queue empty</a></li>
    <li class="divider"></li> 
    % end
    <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/queue" target="_blank">See publishing queue</a></li>
    <li><a href="#" onclick="toggle_queue_runner();">Auto run queue: <span id="auto_queue_run_lbl" class="label label-info">ON</span></a></li>
    <li class="divider"></li>
    % end
    
    % if blog is not None:
    <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/republish" target="_blank">Republish blog</a></li>
    <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/purge" target="_blank">Purge and republish blog</a></li>
    
    % elif site is not None:
    <li><a href="{{settings.BASE_URL}}/site/{{site.id}}/purge">Purge and republish site</a></li>
    
    % else:
    <li><a href="{{settings.BASE_URL}}/system/purge">Purge and republish all sites</a></li>
    % end
  </ul>
</li>  