<div class="form-group">
<span class="pull-right" id="save_animation"></span>
    <label for="publishing_mode">Publishing mode:</label>
    <input type="hidden" id="save" name="save" value="0">
    <select class="form-control input-sm unsaved" id="publishing_mode" name="publishing_mode">
    % for m in publishing_mode.modes:
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
            <button onclick="template_save(1)" type="button" name="save" value="1" class="btn btn-sm btn-warning">Save</button>
        </div>
    </div>
    <div class="form-group">
        <div class="btn-group">
            <button onclick="template_save(3)" type="button" name="save" value="3" class="btn btn-sm btn-success">Save & publish</button>
        </div>
    </div>

    <div class="form-group">
        <div class="btn-group">
            <button type="button" name="preview" id="preview" class="btn btn-sm btn-info">Preview</button>
        </div>
    </div>

    <div class="form-group">
        <div class="btn-group">
            <button onclick="template_save(4)" type="button" name="save" value="4" class="btn btn-sm btn-danger">Delete</button>
        </div>
    </div>
</div>