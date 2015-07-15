% include('header.tpl')
% include('header_messages.tpl')
<div class="container">
<h2>{{settings.PRODUCT_NAME}} installation data</h2><hr/>
<h3>System information</h3>
	% for n in environ_list:
	<div class="col-xs-12">
	    <div class="col-xs-3">
	    {{n[0]}}
	    </div>
	    <div class="col-xs-9">
	    {{n[1]}}
	    </div>
	</div>
	% end
<h3>Installation information</h3>
    % for n in settings_list:
    <div class="col-xs-12">
        <div class="col-xs-3">
        {{n[0]}}
        </div>
        <div class="col-xs-9">
        {{n[1]}}
        </div>
    </div>
    % end
</div>
% include('footer.tpl')