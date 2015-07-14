<div id="messages-inner" class="col-xs-12">
% if status:
<div id="alert_message" class="alert alert-{{status.type}}" role="alert">
<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
<span class="glyphicon glyphicon-{{status.icon}}"></span>
{{!status.message}}
</div>
%end
</div>