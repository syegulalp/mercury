% include('header.tpl')
% include('header_messages.tpl')
<div class="xcontainer">
<div class="col-xs-12">
	<h3>Hello, {{user.name}}</h3><hr/>
	<div class="col-xs-9" id="recent_pages">
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
		    <td>{{utils.date_format(page.modified_date)}}</td>
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
   <div class="col-xs-3" id="your_blogs">
        <h4>Blogs you contribute to:</h4>
        <ul>
        %for blog in your_blogs:
            <li>{{!blog.for_display}} / {{!blog.site.for_display}}
        %end
        </ul>
        <hr/>
    </div>
</div>
</div>
% include('footer.tpl')