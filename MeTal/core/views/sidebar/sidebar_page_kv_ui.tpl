<div id="kv_list">
% if kv_ui is not None:
{{!kv_ui}}
<br/>
% else:
<p>[<i>No key-value pairs</i>]</p>
% end
</div>
<div class="form-group">
    <label for="new_key_name">Key</label>
    <input class="form-control" id="new_key_name" name="new_key_name" placeholder="Key name">
  <div class="form-group">
    <label for="new_key_value">Value</label>
    <input class="form-control" id="new_key_value" name="new_key_value" placeholder="Key value">
  </div>
  <button onclick="add_kv();" type="button" class="btn btn-primary">Add
  <span id="kv_activity" style="display:none" class=""></span>
  </button>
</div>