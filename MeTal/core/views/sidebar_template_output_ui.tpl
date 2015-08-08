<div class="form-group">
    % if template.template_type == types.index:
    % for n in template.default_mapping.fileinfos:
    <p id="output_{{n.id}}">
    {{!utils.breaks(n.url)}}
        <a href="{{n.url}}" target="_blank">
        <span class="glyphicon glyphicon-new-window"></span>
        </a>
    % end
    % else:
    <p><a href="#">See all output files generated.</a></p>
    % end
</div>
