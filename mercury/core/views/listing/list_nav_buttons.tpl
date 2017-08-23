% if action:
% if top_line:
% margin="margin: .75em 0 0 0;"
% else:
% margin="margin: 0 0 .75em 0;"
% end
% else:
% margin=""
% end
<div class="row"  style="{{margin}}">
    % #<div class="col-sm-12">
    <span id="list_nav_action">
    % if action:
    {{!action}}
    % end
    </span>
    % # </div>    
</div>