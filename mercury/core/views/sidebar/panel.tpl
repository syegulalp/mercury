<div class="panel panel-default">
    <a class="collapsed" data-toggle="collapse" data-parent="#accordion" href="#{{label}}_collapse" aria-expanded="false" aria-controls="{{label}}_collapse">
        <div class="panel-heading editor-sidebar" role="tab" id="#{{label}}_categories_tab">
            <p class="panel-title"><span class="glyphicon glyphicon-{{icon}} editor-sidebar"></span>{{title}}</p>
    	</div>
    </a>

    <div id="{{label}}_collapse" class="panel-collapse collapse{{collapse}}" role="tabpanel" aria-labelledby="{{label}}_tab">
        <div class="panel-body">
        {{!body}}
        </div>
    </div>    
</div>