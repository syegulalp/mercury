<div class="form-group">
    <label for="publishing_mode">Publishing mode:</label>
    <select class="form-control input-sm unsaved" id="publishing_mode" name="publishing_mode">
    % for m in modes:
        % selected=""
        % if m == template.publishing_mode:
        % selected="selected"
        % end
        <option {{selected}} value="{{m}}">{{m}}</option>
    % end
    </select>
</div>

<div class="hide-overflow">
    <div class="form-group">
        <div class="btn-group">
            <button type="submit" name="save" value="1" class="btn btn-sm btn-primary">Save</button>
        </div>
    </div>
    <div class="form-group">
        <div class="btn-group">
            <button type="submit" name="save" value="2" class="btn btn-sm btn-danger">Save & publish</button>
        </div>
    </div>
</div>
