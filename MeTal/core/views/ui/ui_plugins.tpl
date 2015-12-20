% include('include/header.tpl')
% include('include/header_messages.tpl')
<form>
<div class="col-xs-12">

	<table class="table table-condensed">
		<thead>
			<tr>
			<th style="width:1%"></th>
			<th>ID</th>
			<th>Plugin name</th>
			<th>Install path</th>
			<th>Status</th>
			</tr>
		</thead>
	% for plugin in plugins:
		<tr>
			<td><input type="checkbox" id="check-{{plugin.id}}" name="check-{{plugin.id}}">
			<td><label for="check-{{plugin.id}}">{{plugin.id}}</label></td>
			<td>
			% if plugin.enabled:
			<b><a href="{{settings.BASE_URL}}/system/plugin/{{plugin.id}}">{{plugin.friendly_name}}</a>
            (v. {{plugin.version}})</b>
            % else:
            <i>{{settings.PLUGIN_FILE_PATH}}{{settings._sep}}{{plugin.path}}</i>
            % end            
			<br><label style="font-weight:normal" for="check-{{plugin.id}}">{{plugin.description}}</label>
			</td>
			<td>{{settings.PLUGIN_FILE_PATH}}{{settings._sep}}{{plugin.path}}</td>
			<td>
			% if plugin.enabled:
			<a href="{{settings.BASE_URL}}/system/plugin/{{plugin.id}}/disable"><span class="label label-success">Enabled</span></a>
			% else:
			<a href="{{settings.BASE_URL}}/system/plugin/{{plugin.id}}/enable"><span class="label label-default">Disabled</span></a>
			% end
		</tr>
	% end
	</table>
</div>
</form>
% include('include/footer.tpl')
