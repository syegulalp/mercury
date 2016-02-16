% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="container-fluid">
    <div class="row">
        <div class="col-md-12">
            <form class="form-horizontal" role="form">
                <div class="form-group">
                    <label for="inputEmail3" class="col-sm-2 control-label">
                        Email
                    </label>
                    <div class="col-sm-10">
                        <input type="email" class="form-control" id="inputEmail3" />
                    </div>
                </div>
                <div class="form-group">
                     
                    <label for="inputPassword3" class="col-sm-2 control-label">
                        Password
                    </label>
                    <div class="col-sm-10">
                        <input type="password" class="form-control" id="inputPassword3" />
                    </div>
                </div>
                <div class="form-group">
                    <div class="col-sm-offset-2 col-sm-10">
                        <div class="checkbox">
                             
                            <label>
                                <input type="checkbox" /> Remember me
                            </label>
                        </div>
                    </div>
                </div>
                <div class="form-group">
                    <div class="col-sm-offset-2 col-sm-10">
                         
                        <button type="submit" class="btn btn-default">
                            Sign in
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
</div>
% include('include/footer.tpl')