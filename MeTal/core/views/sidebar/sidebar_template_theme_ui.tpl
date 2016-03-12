<div id="theme_group" class="form-group">
    <label for="template_ref">Original theme template:</label>
    <p id="template_ref">
        {{template.template_ref}}
    </p>
    
    <div class="form-group">
        <div class="btn-group">
            <a href="{{settings.BASE_URL}}/template/{{template.id}}/refresh"><button type="button" class="btn btn-sm btn-warning">Refresh from template</button></a>
        </div>
    </div>    
</div>
