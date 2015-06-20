<div class="form-group">
    <label for="publication_status">Publication status:</label>
    <select class="form-control input-sm unsaved" id="publication_status" name="publication_status">
    % for status in status_modes.statuses:
        % selected=""
        % if status[0] == page.status_id:
        % selected="selected"
        % end
        <option {{selected}} value="{{status[0]}}">{{status[1]}}</option>
    % end
    </select>
</div>
    
<div class="form-group">
    <label for="publication_date">Publication date:</label>
    <div class='input-group input-group-sm date' id='publication_date_picker'>
       <input type="datetime" class="form-control unsaved entersubmit" id="publication_date" placeholder=""
          name="publication_date" value="{{utils.date_format(page.publication_date)}}" />
       <span class="input-group-addon">
           <span class="glyphicon glyphicon-calendar"></span>
       </span>
   </div>
</div>

<div class="form-group">
    <label for="basename">Basename:</label>
    <div class="input-group">
        <input title="Click icon to unlock basename" type="text" class="form-control input-sm unsaved entersubmit" id="basename" disabled="disabled"
            name="basename" value="{{page.basename}}">
        <span class="input-group-btn">
            <button title="Edit basename" onclick="$('#basename').prop('disabled', false);" class="btn btn-sm" type="button"><span class="glyphicon glyphicon-edit"></span></button>
        </span>
    </div>
</div>
    
<div class="form-group">
    <label for="permalink">Permalink:</label>
    <p id="permalink">
        % if page.id is None:
        [<i>Save page to create a permalink</i>]
        % else:
        {{!utils.breaks(page.permalink)}}
        % if page.status_id == 2:
        <a title="See preview or live page" href="{{page.preview_permalink}}" target="_blank">
        <span class="glyphicon glyphicon-new-window"></span>
        % end
        % end
        </a>
    </p>
</div>
    
<div class="form-group">
    <label for="change_note">Change note: <small>(optional)</small></label>
    <input type="text" class="form-control input-sm unsaved entersubmit" id="change_note" placeholder=""
        name="change_note" value="" />
</div>

<div class="form-group" style="line-height: 2.5em;">
    <input type="hidden" id="save" name="save" value="{{page.status_id}}">
    <div class="btn-group">
        <button onclick="page_save({{save_action[page.status_id][0]}})" type="button" accesskey="s"
            id="save_button" class="btn btn-sm btn-{{status_badge[page.status_id]}}">
            {{save_action[page.status_id][1]}}
            <div id="save_animation"></div>
            </button>                           
        <button type="button" class="btn btn-sm btn-{{status_badge[page.status_id]}} dropdown-toggle"
        data-toggle="dropdown" aria-expanded="false">
        <span class="caret"></span>
        <span class="sr-only">Toggle Dropdown</span>
        </button>
        <ul class="dropdown-menu" role="menu">
            % if page.status_id == 2:
            <li><a onclick="page_save({{save_actions.SAVE_TO_DRAFT}})" href="#">Save draft only</a></li>
            % else:
            <li><a onclick="page_save({{save_actions.SAVE_TO_DRAFT + save_actions.UPDATE_LIVE_PAGE}})" href="#">Save and publish</a></li>
            % end
            <li><a onclick="page_save({{save_actions.SAVE_TO_DRAFT + save_actions.EXIT_EDITOR}})" href="#">Save and exit</a></li>
            <li><a onclick="page_save({{save_actions.EXIT_EDITOR}})" href="#">Exit without saving</a></li>
            % if page.status_id == 2:
            <li><a onclick="page_save({{save_actions.UNPUBLISH_PAGE}})" href="#">Unpublish</a></li>
            % end
            <li><a onclick="page_save({{save_actions.DELETE_PAGE}})" href="#">Delete</a></li>
        </ul>
    </div>
    % if page.id is not None:
    <div class="btn-group">
        <button type="button" onclick="show_local_preview()" accesskey="p" id="preview_button" class="btn btn-sm btn-primary">Preview</button>
        <button type="button" id="preview_dropdown" class="btn btn-sm btn-primary dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
        <span class="caret"></span>
        <span class="sr-only">Toggle Dropdown</span>
        </button>
        <ul class="dropdown-menu" role="menu">
            <li><a onclick="show_local_preview()" href="#">Local preview</a></li>
            <li><a href="#">Shared preview</a></li>
        </ul>
    </div>
    % end
</div>