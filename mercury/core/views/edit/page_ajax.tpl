% include('include/page_title.tpl')
% include('include/header_messages.tpl')
<div id="sidebar_inner">
% if queue.count() and _save_action & _save_action_list.UPDATE_LIVE_PAGE:
<script type="text/javascript">
run_queue({{blog.id}});
</script>
% end
{{!sidebar}}
</div>
% include('queue/queue_counter_include2.tpl')
