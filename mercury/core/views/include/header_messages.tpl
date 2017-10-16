% if status:
% if msg_float:
<div id="messages_float">
% else:
<div id="messages" class="col-xs-12">
% end
<div id="alert_message" class="alert alert-{{status.type}}" role="alert">
<span class="glyphicon glyphicon-{{status.icon}}"></span>
% if status.close is True: 
<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>
% end
{{!status.message}}
% if status.message_list is not None:
<ul>
% for msg in status.message_list:
<li>{{msg}}</li>
% end
</ul>
% end
% if status.action is not None:
<hr/>
<a href="{{status.url}}">
<button type="button" class="btn btn-sm btn-success" >
{{status.action}}
</button>
</a>
% end
% if status.confirm is not None:
<hr/>
<form id="confirm_form" name="confirm_form" method="post">{{!csrf_token}}
<button type="submit" class="btn btn-sm btn-danger" id="confirm_{{status.confirm['id']}}"
name="{{status.confirm['name']}}"
value="{{status.confirm['value']}}">{{!status.confirm['label']}}</button>
<span class="pull-right">
<a href="{{status.deny['url']}}">
<button type="button" class="btn btn-sm btn-success" >
{{!status.deny['label']}}
</button>
</a>
</span>
</form>
% end
</div>
</div>
% end