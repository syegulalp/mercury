<div id="modal_contents" class="modal fade">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
        <h4 class="modal-title">Revisions for page #{{ page.id }}</h4>
      </div>
      <div class="modal-body">
      % if page.revisions.count()>0:
      <ol>
        % for page in page.revisions:
        <li><a href="{{settings.BASE_URL}}/page/{{page.page_id}}/edit/restore/{{page.id}}">{{ utils.date_format(page.modified_date)}}</a>
        % if page.change_note:
        (<i>{{page.change_note}}</i>)
        % end
        [{{page.saved_by_user.name}}]
        </li>
        % end
      </ol>
      % else:
      [<i>No earlier revisions found for this page</i>]
      % end
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>