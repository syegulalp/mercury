% include('include/header.tpl')
<div class="col-xs-12">
% include('include/header_messages.tpl')

    % try:
    % for k in report:
    <p>{{!k}}
    % end
    % except:
    % pass
    % end

</div>
% include('include/footer.tpl')