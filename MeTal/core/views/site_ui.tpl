% include('header.tpl')
% include('header_messages.tpl')
<div class="col-xs-12">

	<table class="table table-condensed">
		<thead>
			<tr>
			<th></th>
			<th>ID</th>
			<th>Title</th>
			</tr>
		</thead>
	% for site in sites:
		<tr>
			<td><input type="checkbox" id="check-{{site.id}}" name="check-{{site.id}}">
			<td>{{site.id}}</td>
			<td><a href="{{settings.BASE_URL}}/site/{{site.id}}">{{site.name}}</a></td>
		</tr>
	% end
	</table>
</div>
% include('footer.tpl')