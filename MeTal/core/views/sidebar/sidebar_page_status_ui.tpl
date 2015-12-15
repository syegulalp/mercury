<div id="status_group" class="form-group">

    <p><span class="label label-{{status_badge[page.status_id]}}">{{page.status}}</span></p>

    <label for="modified_date">Last saved:</label>
    <p id="modified_date">
        {{utils.date_format(page.modified_date_tz)}}
    </p>
    
    <label for="created_date">Originally created:</label>
    <p id="created_date">
        {{utils.date_format(page.created_date_tz)}}
    </p>
    
    % if page.status_id == 2:
    <label for="publication_date">Published on:</label>
    <p id="publication_date">
        {{utils.date_format(page.publication_date_tz)}}
    </p>
    % end
    
    <label for="author">Author:</label>
    <p id="author">
        {{page.user.name}}
    </p>
    
    <p><small><a id="revision_link" href="#">See earlier revisions</a></small></p>
    
</div>