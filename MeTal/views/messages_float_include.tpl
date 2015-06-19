% try:
% msg_float
% except NameError:
% _id="messages"
% _class="col-xs-12"
% else:
% _id="messages_float"
% _class=""
% end
<div id="{{_id}}" class="{{_class}}">
% if status:
<div id="alert_message" class="alert alert-{{status.type}}" role="alert">
<span class="glyphicon glyphicon-{{status.icon}}"></span>
{{!status.message}}
<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
</div>
%end
</div>