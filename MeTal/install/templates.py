templates = (

    {
        "title":"Index Template",
        "default_mapping":"{{blog.index_file}}",
        "publishing_mode":1,
        "body":"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{{blog.name}}</title>
    </head>
    <body>
        <h3>{{blog.name}}</h3>
        {{blog.description}}
        <hr/>
        <p>Entries
        % for p in blog.last_n_pages(0):
        <p><a href="{{p.permalink}}">{{p.title}}</a> / {{p.publication_date}}<hr/>
        % end
        &copy; 2014. All wrongs reversed.
    </body>
</html>
    """},
    
    {
        "title":"Page Template",
        "default_mapping":"%Y/%m/{{page.basename}}",
        "publishing_mode":1,
        "body":"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{{page.title}} | {{blog.name}}</title>
    </head>
    <body>
        <h3>{{!page.title}}</h3><hr/>
        {{!page.text}}<hr/>
        <a href='{{blog.url}}'>Home</a>
    </body>
</html>
    """},
    
    {
        "title":"Monthly Archive Template",
        "default_mapping":"%Y/%m/{{blog.index_file}}",
        "publishing_mode":1,
        "body":"""
<p>Date-based archive to come
<a href='{{blog.url}}'>Home</a>
    """}

)