function init_typeahead(target_name){

    var tags = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      remote: {
        url: global.base,
        prepare: function(query,settings){
            settings.url = global.base+'/api/1/get-tag/'+query+'?blog='+global.blog;
            $('#tag_activity').show();
            return settings;
        },
        transform: function(response){
            $('#tag_activity').hide();
            return response;
        }
      }
    });
    
	$('.typeahead').typeahead(null, {
		  name: 'tags',
		  source: tags,
		  display: 'tag'
		});	
        
}
