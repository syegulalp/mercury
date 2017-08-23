<div id="page_save_group" class="form-group" style="line-height: 2.5em;">
    <input type="hidden" id="save" name="save" value="{{page.status_id}}">
    <input type="hidden" id="backup" name="backup" value="N">
    <div class="btn-group btn-block">
        <button onclick="page_save({{save_action[page.status_id][0]}})" type="button" accesskey="s"
            id="save_button" class="btn btn-sm btn-{{status_badge[page.status_id]}} col-xs-10">
            {{save_action[page.status_id][1]}}
            <div id="save_animation"></div>
            </button>
        <button type="button" class="btn btn-sm btn-{{status_badge[page.status_id]}} dropdown-toggle col-xs-2"
        data-toggle="dropdown" aria-expanded="false">
        <span class="caret"></span>
        <span class="sr-only">Toggle Dropdown</span>
        </button>
        <ul class="dropdown-menu col-xs-10" role="menu">
            % if page.status_id == 2:
            <li><a title="Save this page to a draft, but do not publish it or make its changes live." onclick="page_save({{save_action_list.SAVE_TO_DRAFT}})" href="#">Save draft only</a></li>
            % else:
            <li><a title="Save this page to a draft, and make the changes live on the website." onclick="page_save({{save_action_list.SAVE_TO_DRAFT + save_action_list.UPDATE_LIVE_PAGE}})" href="#">Save and publish</a></li>
            % end
 <!--
            <li><a title="Save this page to a draft, release the editing lock, and leave the editor." onclick="page_save({{save_action_list.SAVE_TO_DRAFT + save_action_list.EXIT_EDITOR}})" href="#">Save and exit</a></li>
            <li><a title="Close the editor without making any further changes to this draft, and release the editing lock." onclick="page_save({{save_action_list.EXIT_EDITOR}})" href="#">Exit without saving</a></li>
-->
            % if page.status_id == 2:
            <li><a title="Remove the live version of this page, and set its status back to Draft." onclick="page_save({{save_action_list.UNPUBLISH_PAGE}})" href="#">Unpublish</a></li>
            % end
            <!-- <li><a title="Remove the live version of this page, and delete its draft and all of its versions as well." onclick="page_save({{save_action_list.DELETE_PAGE}})" href="#">Delete</a></li>
            -->
        </ul>
    </div>
    % if page.id is not None:
    
    <div id="preview_group" class="btn-group btn-block">
        <button type="button" onclick="save_draft_and_preview()" accesskey="p" id="preview_button" class="btn btn-sm btn-primary col-xs-10">Save draft and preview</button>
        <button type="button" class="btn btn-sm btn-primary dropdown-toggle col-xs-2"
        data-toggle="dropdown" aria-expanded="false">
        <span class="caret"></span>
        <span class="sr-only">Toggle Dropdown</span>
        </button>
        <ul class="dropdown-menu col-xs-10" role="menu">
            <li><a title="Render preview of existing saved draft." onclick="show_preview_only()"
            href="#">Preview only (no save)</a></li>
        </ul>
    </div>    
    % end
</div>

<div id="publication_status_group" class="form-group">
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

<div id="publication_date_group" class="form-group">
    <label for="publication_date">Publication date:</label>
    <div class='input-group input-group-sm date' id='publication_date_picker'>
       <input type="datetime" class="form-control unsaved entersubmit" id="publication_date" placeholder=""
          name="publication_date" value="{{utils.date_format(page.publication_date_tz)}}" />
       <span class="input-group-addon">
           <span class="glyphicon glyphicon-calendar"></span>
       </span>
   </div>
</div>

<div id="basename_group" class="form-group">
    <label for="basename">Basename:</label>
    <div class="input-group">
        <input title="Click icon to unlock basename" type="text" class="form-control input-sm unsaved entersubmit" id="basename" disabled="disabled"
            name="basename" value="{{page.basename}}">
        <span class="input-group-btn">
            <button title="Edit basename" onclick="$('#basename').prop('disabled', false);" class="btn btn-sm" type="button"><span class="glyphicon glyphicon-edit"></span></button>
        </span>
    </div>
</div>

<div id="permalink_group" class="form-group">
    <label for="permalink">Permalink:</label>
    <p id="permalink">
        % if page.id is None:
        [<i>Save page to create a permalink</i>]
        % else:
        {{!utils.breaks(page.permalink)}}
        % if page.status_id != 2:
        % preview_link = page.preview_permalink
        % preview_text = "See preview"
        % else:
        % preview_link = page.permalink
        % preview_text = "See live page"
        % end
        <a title="{{preview_text}}" href="{{preview_link}}" target="_blank">
        <span class="glyphicon glyphicon-new-window"></span>
        % end
        </a>
    </p>
</div>

<div id="change_note_group" class="form-group">
    <label for="change_note">Change note: <small>(optional)</small></label>
    <input type="text" class="form-control input-sm unsaved entersubmit" id="change_note" placeholder=""
        name="change_note" value="" />
</div>


<div class='pull-right'><small>
% if page.status_id==1:
<a href='/page/{{page.id}}/delete'>Delete
<span class="glyphicon glyphicon-trash"></span>
</a>
% else:
To enable deletion, unpublish page
<span class="glyphicon glyphicon-trash"></span>
% end
</small></div>


