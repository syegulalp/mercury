% include('page_title_include.tpl')
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
% #queue_count = queue.count()
% include('queue/queue_counter_include.tpl')