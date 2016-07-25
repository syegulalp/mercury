% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="container-fluid">
    <div class="row">
        <div class="col-md-12">
            <form class="form-horizontal" role="form" method="POST">
            {{!csrf_token}}
            <div class="form-group">
                <label for="import_path" class="col-sm-2 control-label">Import path</label>
                <div class="col-sm-9">
                    <input type="text" class="form-control" aria-describedby="import_path_help"
                    value="{{import_path}}"
                    id="import_path" name="import_path">
                    <span id="import_path_help" class="help-block">The path to the JSON to import.</span>
                </div>
            </div>
                
                <div class="form-group">
                    <div class="col-sm-offset-2 col-sm-10">
                        <button type="submit" class="btn btn-default">
                            Import
                        </button>
                    </div>
                </div>
                
            </form>
        </div>
    </div>
</div>
% include('include/footer.tpl')