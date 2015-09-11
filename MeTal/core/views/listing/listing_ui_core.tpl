<div class="col-xs-12">
% include('listing/list_nav.tpl')
<div style="width:100%; padding-bottom:8px;border-bottom: 1px solid rgb(221,221,221)">
</div>
    <fieldset>
        <table class="table table-condensed table-striped table-hover" style="margin-bottom:0px">
            <colgroup>
            <col width="1%">
            <col width="1%">
            % for col in cols:
                % colclass = " class='{}'".format(col['colclass']) if 'colclass' in col else ''
                % if 'colwidths' in col:
                    % for colx in col['colwidths']:
                    % colwidth = " width={}".format(colx)
                    <col{{colclass}}{{colwidth}}>
                    % end
                % else:
                % colwidth = " width={}".format(col['colwidth']) if 'colwidth' in col else ''
                <col{{colclass}}{{colwidth}}>
                % end
            % end
            </colgroup>
            <thead>
                <tr>
                <th><input type="checkbox" id="check-all" name="check-all" onclick="$(this).closest('fieldset').find(':checkbox').prop('checked', this.checked);"></th>
                <th>ID</th>
                % for col in cols:
                % label_style = " style='"+col['label_style']+"'" if 'label_style' in col else ""
                % label_colspan= " colspan='"+col['label_colspan']+"'" if 'label_colspan' in col else ""
                <th{{!label_style}}{{!label_colspan}}>{{col['label']}}</th>
                % end
                </tr>
            </thead>
            % if rowset.count()==0:
            <tr><td colspan="{{len(cols)+3}}">
                <center>{{colset['none']}}</center>
            </td></tr>
            % else:
                % for row in rowset:
                % rowclass = " class={}".format(colset['rowclass']) if 'rowclass' in colset else ''
                <tr{{rowclass}}>
                    <td><input type="checkbox" id="check-{{row.id}}" name="check-{{row.id}}">
                    <td>{{row.id}}</td>
                    % for col in cols:
                        % colclass = ' class="{}"'.format(col['colclass']) if 'colclass' in col else ''
                        % if 'format_raw' in col:
                        % item = col['format_raw'](row)
                        % else:
                        % item = col['format'](row)
                        % end
                        % if 'format_raw' in col:
                        <td{{!colclass}}>{{!item}}</td>
                        % else:
                        <td{{!colclass}}>{{item}}</td>
                        % end
                    %end
                </tr>
                %end
            %end
        </table>
    </fieldset>
<div style="width:100%; padding-top:8px;border-top: 1px solid rgb(221,221,221)">
</div>
% include('listing/list_nav.tpl')
<br>    
</div>