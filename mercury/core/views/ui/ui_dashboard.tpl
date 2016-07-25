% include('include/header.tpl')
% include('include/header_messages.tpl')
<div class="xcontainer">
<div class="col-xs-12">
	<h3>Hello, {{user.name}}</h3><hr/>
	<div class="col-sm-9" id="your_recent_pages">
	    <h4>Recently edited pages:</h4>
	    <table class='table table-striped table-hover'>
	    % if recent_pages.count()>0:
		    <thead>
		    <tr>
		    <th>Title</th>
		    <th>Last edited on</th>
		    <th>Blog</th>
		    <th>Site</th>
		    </tr>
		    </thead>
		    %for page in recent_pages:
		    <tr>
		    <td>{{!page.for_display}}</td>
		    <td>{{utils.date_format(page.modified_date_tz)}}</td>
		    <td>{{!page.blog.for_display}}</td>
		    <td>{{!page.blog.site.for_display}}</td>
		    </tr>
	    %end
	    %else:
	       <tr><td colspan="4">[<i>No recent blog posts</i>]</td></tr>
	    %end	    
	    </table>
	    <hr/>
   </div>
   <div class="col-sm-3" id="your_actions">
        <h4>Create a new page on:</h4>
        <ul>
        %for blog in your_blogs:
            <li><a href="{{settings.BASE_URL}}/blog/{{blog.id}}/newpage">{{!blog.as_text}}</a>
        %end
        </ul>
        <hr/>
   </div>   
   <div class="col-sm-3" id="your_blogs">
        <h4>Blogs you contribute to:</h4>
        <ul>
        %for blog in your_blogs:
            <li><a target="_blank" href="{{!blog.url}}"><span class="glyphicon glyphicon-new-window"></span></a> {{!blog.for_display}}<br/><small>{{!blog.site.for_display}}</small>
        %end
        </ul>
        <hr/>
    </div>
</div>
</div>
% include('include/footer.tpl')