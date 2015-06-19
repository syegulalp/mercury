<div class="col-xs-12" style="margin-bottom: 2em"></div>
<footer class="footer">
    <div class="col-xs-12 text-muted">
  
		% if settings.DEBUG_MODE:
		
		<div class="pull-right">
			<span class="label label-danger">
			<b>Debug mode</b>
			</span>
		</div>
		% end
		
		% if settings.DESKTOP_MODE:
		<div class="pull-right">
			<span class="label label-primary">
			<b>Desktop mode</b> (<a style="color: yellow" target="_blank" href="http://{{request.environ['HTTP_HOST']}}">{{request.environ['HTTP_HOST']}}</a>)
			</span>
		</div>
		% end
		
		<div class="">
	        <img style="display:inline" src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/images/metal-logo.png">
	        <a href="https://github.com/syegulalp/MeTal"><b>{{settings.PRODUCT_NAME}}</b></a> | &copy; {{settings.__copyright_date__}} {{settings.__author__}}
        </div>
    </div>
</footer>
</body>
</html>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/jquery.min.js"></script>
<script src="{{settings.BASE_URL}}{{settings.STATIC_PATH}}/js/bootstrap.min.js"></script>