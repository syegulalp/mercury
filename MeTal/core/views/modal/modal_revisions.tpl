% rebase('modal/modal_contents.tpl', title=title)
      % if page.revisions.count()>0:
      <ol>
        % for page in page.revisions:
        <li><a href="{{settings.BASE_URL}}/page/{{page.page.id}}/edit/restore/{{page.id}}">{{ utils.date_format(page.modified_date)}}</a>
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