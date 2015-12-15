<div id="template_status_group" class="form-group">
    <p>Publishing mode: <span class="label label-{{publishing_mode.description[template.publishing_mode]['label']}}">{{template.publishing_mode}}</span></p>

    <label for="modified_date">Last saved:</label>
    <p id="modified_date">
        {{utils.date_format(template.modified_date_tz)}}
    </p>

    <label for="template_type">Template type:</label>
    <p id="template_type">
        {{template.template_type}}
    </p>

    <p><small><a id="revision_link" href="#">See earlier revisions</a></small></p>

</div>
