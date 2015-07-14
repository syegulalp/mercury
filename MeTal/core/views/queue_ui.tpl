% include('header.tpl')
% include('header_messages.tpl')
<div class="col-xs-12">
% include('list_nav.tpl')

<div style="width:100%; padding-bottom:8px;border-bottom: 1px solid rgb(221,221,221)">
</div>

    <fieldset>
        <table class="table table-condensed table-striped table-hover" style="margin-bottom:0px">
            <thead>
                <tr>
                <th style="width:1%"><input type="checkbox" id="check-all" name="check-all" onclick="$(this).closest('fieldset').find(':checkbox').prop('checked', this.checked);"></th>
                <th style="width:1%">ID</th>
                <th style="width:1%">Priority</th>
                <th style="width:10%">Job type</th>
                <th>Description</th>
                <th>Date inserted</th>
                
                </tr>
            </thead>
            % if not queue_list.count():
            <tr><td colspan="6">
            <center>[<i>No items pending in queue.</i>]</center>
            </td></tr>
            % else:
            % for row in queue_list:
            <tr>
                <td><input type="checkbox" id="check-{{row.id}}" name="check-{{row.id}}">
                <td>{{row.id}}</td>
                <td>{{row.priority}}</td>
                <td>{{job_type[row.job_type]}}</td>
                <td>{{row.data_string}}</td>
                <td>{{row.date_touched}}</td>
            </tr>
            % end
            % end

        </table>
    </fieldset>

<div style="width:100%; padding-top:8px;border-top: 1px solid rgb(221,221,221)">
</div>

% include('list_nav.tpl')
<br>    
</div>

% include('footer.tpl')
<script async src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/editor.js"></script>