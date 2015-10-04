% include('include/header.tpl')
<div class="col-xs-12">

	% if confirmation is not None:
	<h3>{{!confirmation.message}}</h3>
	<p>{{!confirmation.details}}</p>
	<hr/>
	<form method='post'>{{!csrf_token}}<input type='hidden' name='confirm' value='y'>
	<span class="pull-right">
	<a href="{{confirmation.no}}"><button type='button' class='btn btn-primary'>No, cancel</button></a>
	</span>
	<button class='btn btn-danger' action='submit'>{{confirmation.yes}}</button>
	</form>
	% end
	
	% if confirmed is not None:
	<h3>{{!confirmed.message}}</h3>
	<a href="{{confirmed.url}}">{{confirmed.details}}</a>
	% end

% include('include/header_messages.tpl')

    % for k in report:
    <p>{{!k}}
    % end

</div>
% include('include/footer.tpl')