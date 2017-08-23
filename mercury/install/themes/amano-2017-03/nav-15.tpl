<div class="row">
  <div class='col-xs-6'>
    % if page.previous_page is not None:
    <p><a href="{{!page.previous_page.permalink}}"><i>Previous:</i> {{!page.previous_page.title}}</a></p>
    %end
  </div>
  <div class='col-xs-6'>
    % if page.next_page is not None:
    <span class='pull-right'>
      <p><a href="{{!page.next_page.permalink}}"><i>Next:</i> {{!page.next_page.title}}</a></p>
    </span>
    % end
  </div>
</div>