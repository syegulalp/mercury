<div id="kv_list">
% if len(kv_ui)>0:
{{!kv_ui}}
<br/>
% else:
<p>[<i>No key-value pairs</i>]</p>
% end
</div>
<div id="kv_group">
    <div class="form-group">
        <label for="new_key_name">Key</label>
        <input class="form-control" id="kv_new_key_name" name="new_key_name" placeholder="Key name">
    </div>
    <div class="form-group">
        <label for="new_key_value">Value</label>
        <input class="form-control" id="kv_new_key_value" name="new_key_value" placeholder="Key value">
    </div>
    <input type="hidden" id="kv_object" name="kv_object" value="{{!kv_object}}">
    <input type="hidden" id="kv_objectid" name="kv_objectid" value="{{!kv_objectid}}">
    <button onclick="add_kv();" type="button" class="btn btn-sm btn-primary">Add
    <span id="kv_activity" style="display:none" class=""></span>
    </button>
</div>