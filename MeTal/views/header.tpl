<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    % include('page_title_include.tpl')
    <link href="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/css/custom.css" rel="stylesheet">
  </head>
  <body>
  
<div id="modal_container"></div>
  
<nav class="navbar navbar-default" style="margin-bottom:8px">
  <div class="">
    <div class="navbar-header">
      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar-collapse">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>


        <ul class="nav navbar-brand visible-xs">MeTal</ul>

      
    </div>
    
    <div class="collapse navbar-collapse" id="navbar-collapse">

        <ul class="nav navbar-text" style="margin-left:0">
            <span class="breadcrumb" style="padding:0;background-color:inherit;">
            {{!menu}}
            </span>
        </ul>
    
      
      
      
      <ul class="nav navbar-nav navbar-right">
             
        
        <li>
        <a title="Search" href="#" onclick="toggle_search();"><span class="glyphicon glyphicon-search"></span><span class="visible-xs-inline">&nbsp;&nbsp;Search</span></a>        
        </li>
        
        <li class="dropdown">
          
          <a href="#" title="Publishing queue status" id="queue_status" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">
          % include('queue_counter_include.tpl')
          <span class="visible-xs-inline">&nbsp;Queue</span>
          </a>
          
          
          <ul class="dropdown-menu" role="menu">
            
            % if blog is not None:
            % if queue.count():
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/publish">Publish items in queue</a></li>
            <li class="divider"></li>
            % else:
            <li class="disabled"><a href="#">Queue empty</a></li>
            <li class="divider"></li>
            % end
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/queue">See publishing queue</a></li>
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/republish">Republish blog</a></li>
            <li class="divider"></li>
            % end
            
            % if blog is not None:
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/purge">Purge and republish blog</a></li>
            
            % elif site is not None:
            <li><a href="{{settings.BASE_URL}}/site/{{site.id}}/purge">Purge and republish site</a></li>
            
            % else:
            <li><a href="{{settings.BASE_URL}}/system/purge">Purge and republish all sites</a></li>
            % end
          </ul>

        </li>
        
        <li class="dropdown">
          <a href="#" title="Create..." class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false"><span style="color:#337ab7" class="glyphicon glyphicon-plus-sign"></span>
          <span class="visible-xs-inline">&nbsp;Create ...</span>
          </a>
         
          <ul class="dropdown-menu" role="menu">
            <li role="presentation" class="dropdown-header" >Create ...</li>
            % if blog:
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/newpage">Page</a></li>
            % elif user.blogs():
            % for b in user.blogs():
            <li><a href="{{settings.BASE_URL}}/blog/{{b.id}}/newpage">Page ({{b.as_text}})</a></li>
            % end
            % end
            <li><a href="#">Media</a></li>
            <li><a href="#">Blog</a></li>
            <li><a href="#">Site</a></li>
          </ul>
        </li>
        
        
        % if blog:
        <li>
          <a title="See the published version of this blog" target="_blank" href="{{blog.permalink}}"><span class="glyphicon glyphicon-new-window"></span>
          <span class="visible-xs-inline">&nbsp;See published blog</span></a>
        </li>
        % elif site:
        <li>
          <a title="See the published version of this site" target="_blank" href="{{site.permalink}}"><span class="glyphicon glyphicon-new-window"></span>
          <span class="visible-xs-inline">&nbsp;See published site</span></a>
        </li>
        % end
        
            <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-expanded="false">
                {{user.name}}&nbsp;&nbsp;<span class="caret"></span></a>
                  <ul class="dropdown-menu" role="menu">
                    <li><a href="{{settings.BASE_URL}}/me/settings">Settings</a></li>
                    <li><a href="{{settings.BASE_URL}}/logout?_={{user.logout_nonce}}">Log out</a></li>
                  </ul>
            </li>      
       
      </ul>
      
    </div><!-- /.navbar-collapse -->
  </div><!-- /.container-fluid -->
</nav>
<div id="search" class="col-xs-12" 
% if search_terms == '':
style="display: none"
% end
>
	<div class="alert alert-info alert-dismissible" role="alert">
		<button type="button" class="close" onclick="toggle_search();" aria-label="Close"><span aria-hidden="true">&times;</span></button>
		<form accept-charset="utf-8" action="{{search_context[0]['form_target'](search_context[1])}}" id="search_form" class="form-inline">
		  <div class="form-group">
		    <label for="search_text">{{search_context[0]['form_description']}}  </label>
		    <div class="input-group">
		      <input name="search" value="{{utils.utf8_escape(search_terms)}}" type="text" class="form-control input-sm" id="search_text" placeholder="{{search_context[0]['form_placeholder']}}">
		      <span onclick="clear_search();" class="input-group-addon">
                <span class="glyphicon glyphicon-remove"></span>                
		      </span>
		    </div>
		  </div>
		<button id="search_button" type="submit" class="btn btn-default btn-sm">Go</button>
		</form>
	</div>
</div>