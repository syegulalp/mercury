function init_typeahead(target_name){

    var tags = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('tag'),
      //datumTokenizer: Bloodhound.tokenizers.whitespace,
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      //local: {'tag':'Test','id':'1'},
      //prefetch: global.base+'/api/1/get-tags/blog/'+global.blog,
      
      prefetch: {
          url: global.base+'/api/1/get-tags/blog/'+global.blog+'/1000',
          prepare: function(settings){
            settings.url = global.base+'/api/1/get-tags/blog/'+global.blog+'/1000';
            $('#tag_activity').show();
            return settings;
          },
          transform: function(response){
            $('#tag_activity').hide();
            return response;
        }
      },
      
      remote: {
        url: global.base,
        prepare: function(query,settings){
            settings.url = global.base+'/api/1/match-tag/blog/'+global.blog;
            $('#tag_activity').show();
            return settings;
        },
        transform: function(response){
            $('#tag_activity').hide();
            return response;
        }
      }
      
    });
    
	$('.typeahead').typeahead({
	hint: false,
	
	}, {
		  name: 'tags',
		  source: tags,
		  display: 'tag',
		  limit: 999,
		});	
        
}
