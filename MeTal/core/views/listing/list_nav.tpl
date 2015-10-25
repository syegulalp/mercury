<div class="row">
    <div class="col-sm-6">
    <span class="dropdown">
      <button class="btn btn-default dropdown-toggle btn-sm" type="button" id="checked_action_menu" data-toggle="dropdown" aria-expanded="true">
        Action on checked items:
        <span class="caret"></span>
      </button>
      <ul class="dropdown-menu btn-sm" role="menu" aria-labelledby="checked_action_menu">
        <li role="presentation"><a role="menuitem" tabindex="-1" href="#">[<i>Not implemented yet</i>]</a></li>
      </ul>
    </span>
    
    <span id="list_nav_action" class="">
    % try:
    {{!action}}
    % except:
    
    % end
    </span>
    </div>    


    <div class="col-sm-6">
    <span class="pull-right pull-conditional">
    
        <ul class="pagination pagination-sm" style="display:inline;">
            <li>
%# eventually use proper URL parameter processing w/a function passed to change page ID & add search query
                <a href="?page=1{{search_query}}" aria-label="First">
                    <span aria-hidden="true"><span class="glyphicon glyphicon-backward"></span> First</span>
                </a>
            </li>
            <li>
                <a href="?page={{paginator['prev_page']}}{{search_query}}" aria-label="Previous">
                    <span aria-hidden="true"><span class="glyphicon glyphicon-chevron-left"></span> Prev</span>
                </a>
            </li>
            <li>
            <a href="#">
            % if not paginator['page_count']:
            None
            % else:
            {{paginator['first_item']}} to {{paginator['last_item']}} of {{paginator['page_count']}}
            % end
            </a>
            </li>
            
            <li>
                <a href="?page={{paginator['next_page']}}{{search_query}}" aria-label="Next">
                    <span aria-hidden="true">Next <span class="glyphicon glyphicon-chevron-right"></span></span>
                </a>
            </li>
            <li>
                <a href="?page={{paginator['max_pages']}}{{search_query}}" aria-label="Last">
                    <span aria-hidden="true">Last <span class="glyphicon glyphicon-forward"></span></span>
                </a>
            </li>
        </ul>
    </span>
    </div>
</div>