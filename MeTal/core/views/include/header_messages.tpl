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
<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
{{!status.message}}
% if status.message_list is not None:
<ul>
% for msg in status.message_list:
<li>{{msg}}</li>
% end
</ul>
% end
% if status.confirm is not None:
<hr/>
<form id="confirm_form" name="confirm_form" method="post">{{!csrf_token}}
<button type="submit" class="btn btn-sm btn-danger" id="confirm_{{status.confirm}}" name="{{status.confirm[0]}}"
value="{{status.confirm[1]}}">Yes, I want to do this</button>
<span class="pull-right">
<button type="submit" class="btn btn-sm btn-success" >No, I don't want to do this</button>
<input type="hidden" name="confirm" value="Y">
</span>
</form>
% end
</div>
% end
</div>