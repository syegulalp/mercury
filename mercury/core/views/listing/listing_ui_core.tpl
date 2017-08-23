<div class="col-xs-12">
% top_line = False
% include('listing/list_nav_buttons.tpl')
% include('listing/list_nav.tpl')
<div style="width:100%; padding-bottom:8px;border-bottom: 1px solid rgb(221,221,221)">
</div>
    <fieldset><form id="listing_form">{{!csrf_token}}
        <table id="listing_table" class="table table-condensed table-striped table-hover" style="margin-bottom:0px">
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
                    <td><input type="checkbox" id="check-{{row.id}}" name="check" value="{{row.id}}">
                    <td><label for="check-{{row.id}}">{{row.id}}</label></td>
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
        </table></form>
    </fieldset>
<div style="width:100%; padding-top:8px;border-top: 1px solid rgb(221,221,221)">
</div>
% top_line = True
% include('listing/list_nav.tpl')
% include('listing/list_nav_buttons.tpl')
<br>    
</div>