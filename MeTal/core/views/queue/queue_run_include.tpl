<div id="progress_inner">
    <div class="progress">
    %if percentage_complete<100:
    %    active="active"
    %else:
    %    active=""
    %end
      <div id="progress_bar" class="progress-bar progress-bar-striped {{active}}" role="progressbar" aria-valuenow="{{percentage_complete}}"
      aria-valuemin="0" aria-valuemax="100"
      style="min-width: 2em; width:{{percentage_complete}}%">
        {{percentage_complete}}%
      </div>
    </div>
    % if percentage_complete>=100:
    <p>Publishing job finished. You may now close this tab or window.
    % else:
    <p>Working ...
    % end
</div>
% if percentage_complete>0:
% include('queue/queue_counter_include.tpl')
% end