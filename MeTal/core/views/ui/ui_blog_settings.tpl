% include('include/header.tpl')
% include('include/header_messages.tpl')
% if blog.id is not None:
% disabled = "disabled='disabled'"
% else:
% disabled = ""
% end
<div class="col-xs-12">

    <form class="form-horizontal" method="post">
    {{!csrf_token}}
    <div class="col-sm-12">
    % include('include/nav_tabs.tpl')
	<br/>
	</div>
	% if nav_default=='basic':
	
        <div class="form-group">
            <label for="blog_name" class="col-sm-2 control-label">Blog name</label>
            <div class="col-sm-9">
                <input type="text" class="form-control" aria-describedby="blog_name_help"
                value="{{blog.name}}"
                id="blog_name" name="blog_name">
                <span id="blog_name_help" class="help-block">The name of your blog.</span>
            </div>
        </div>
        
        <div class="form-group">
            <label for="blog_description" class="col-sm-2 control-label">Description</label>
            <div class="col-sm-9">
                <input type="text" class="form-control" aria-describedby="blog_description_help"
                value="{{blog.description}}"
                id="blog_description" name="blog_description">
                <span id="blog_description_help" class="help-block">A short description of your blog, for SEO use.</span>
            </div>
        </div>
        
        <div class="form-group">
            <label for="blog_timezone" class="col-sm-2 control-label">Blog timezone</label>
            <div class="col-sm-9">
            	<select id="blog_timezone" name="blog_timezone" class="form-control" aria-describedby="blog_timezone_help">
            	% for m,n in enumerate(timezones):
            	% selected=''
            	% if n==blog.timezone:
            	% selected=' selected'
            	% end
            	<option value="{{m}}"{{selected}}>{{!n}}</option>
            	% end
            	</select>
                <span id="blog_timezone_help" class="help-block">Timezone for your blog. Default is UTC.</span>
            </div>
        </div>  
        
    % elif nav_default=='dirs':
        <div class="form-group">
            <label for="blog_url" class="col-sm-2 control-label">URL</label>
            <div class="col-sm-9">
                <div class="input-group">
                    <input title="Click the icon at the right to unlock this field" type="url" class="form-control" {{disabled}}
                    value="{{blog.url}}" aria-describedby="blog_url_help"
                    id="blog_url" name="blog_url">
                    <span class="input-group-btn">
                        <button title="Edit URL" onclick="$('#blog_url').prop('disabled', false);" class="btn" type="button">
                        <span class="glyphicon glyphicon-edit"></span></button>
                    </span>
                    
                </div>
                <span id="blog_url_help" class="help-block">The URL others will use to access your blog, without trailing slashes.<br>
                % if blog.id is not None:
                <b>Changing this may break links within your blog.</b>
                % end
                </span>
                
            </div>
        </div>
        
        <div class="form-group">
            <label for="blog_path" class="col-sm-2 control-label">Filepath</label>
            <div class="col-sm-9">
                <div class="input-group">
                    <input title="Click the icon at the right to unlock this field" type="text" class="form-control" {{disabled}}
                    value="{{blog.path}}" aria-describedby="blog_path_help"
                    
                    id="blog_path" name="blog_path" placeholder="">
                    <span class="input-group-btn">
                        <button title="Edit URL" onclick="$('#blog_path').prop('disabled', false);" class="btn" type="button">
                        <span class="glyphicon glyphicon-edit"></span></button>
                    </span>
                </div>
                <span id="blog_path_help" class="help-block">The filepath to where the blog's files will be published.<br>
                % if blog.id is not None:
                <b>Don't change this unless you know what you're doing.</b>
                % end
                </span>
            </div>
        </div>        
        
        <div class="form-group">
            <label for="blog_base_extension" class="col-sm-2 control-label">Extension</label>
            <div class="col-sm-9">
                <div class="input-group">
                    <input title="Click the icon at the right to unlock this field" type="text" class="form-control" {{disabled}}
                    value="{{blog.base_extension}}" aria-describedby="blog_base_extension_help"
                    
                    id="blog_base_extension" name="blog_base_extension"
                    placeholder="Default file extension used for generated blog files (usually 'html').">
                    <span class="input-group-btn">
                        <button title="Edit URL" onclick="$('#blog_base_extension').prop('disabled', false);" class="btn" type="button">
                        <span class="glyphicon glyphicon-edit"></span></button>
                    </span>
                </div>
                <span id="blog_base_extension_help" class="help-block">The file extension used for files in your blog, without a leading dot.<br>
                % if blog.id is not None:
                <b>Don't change this either unless you know what you're doing.</b>
                % end
                </span>
            </div>
        </div>
        
        <div class="form-group">
            <label for="blog_media_path" class="col-sm-2 control-label">Media path</label>
            <div class="col-sm-9">
                <input type="text" class="form-control" aria-describedby="blog_media_path_help"
                value="{{blog.media_path}}"
                id="blog_media_path" name="blog_media_path">
                <span id="blog_media_path_help" class="help-block">Path within your blog to where media will be uploaded.<br/>This can be a simple string or any valid expression used for a template mapping (e.g., <code>media/%Y</code>).</span>
            </div>
        </div>       
        
         
        
        % end
        <div class="form-group">
            <div class="col-sm-offset-2 col-sm-9">
                <button type="submit" class="btn btn-primary">Save changes</button>
            </div>
        </div>
        
        <hr/>            
                    
    </form>

</div>
% include('include/footer.tpl')