% include('include/page_title.tpl')
<div id="messages">
% include('include/header_messages.tpl')
</div>
<div id="sidebar_inner">
% if queue.count():
<script type="text/javascript">
run_queue({{blog.id}});
</script>
% end
{{!sidebar}}
</div>
% include('queue/queue_counter_include2.tpl')