function init_typeahead(target_name){

    var tags = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      remote: {
        url: global.base+'/api/1/get-tag/%QUERY?blog='+global.blog,
        wildcard: '%QUERY'
      }
    });

	$('.typeahead').typeahead(null, {
		  name: 'tags',
		  source: tags,
		  display: 'tag'
		});
		
}
