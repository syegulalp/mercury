<div id="upload_progress" class="progress" style="display:none">
    <div id="upload_progress_bar" class="progress-bar progress-bar-striped active" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%">
        <span id="upload_progress_text"></span>
    </div>
</div>
% if page.id:
<div class="well uploadarea"><small><center>Drop images here to upload</center></small></div>
<div id="media_list">
    % include('edit/page_media_list.tpl')
</div>
<small><a id="insert_media_link" href="#">Add existing media</a></small>
% else:
<p>[<i>You must save this page before you can add media to it</i>]</p>
% end