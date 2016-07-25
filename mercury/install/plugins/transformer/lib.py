import re

# to be loaded from db at plugin import

# TODO: swap all quotes outside of brackets for &quot;

transformations = (
    (re.compile(r'(\s?)--(\s?)'), '—'),
    (re.compile(r'(\s|&nbsp;|^|>)&quot;([^\.,;:?!])', re.M), r'\1“\2'),
    (re.compile(r'&quot;', re.M), r'”?'),
    (re.compile(r'(\s|&nbsp;|^|>)&#39;', re.M), r'\1‘'),
    (re.compile(r'&#39;', re.M), r'’'),
    (re.compile(r'&nbsp;'), ' '),
    (re.compile(r' ?\.\.\. ?'), '…'),
    (re.compile(r'<a(.*?)href="search:([^"]*)"(.*?)>'),
     r'<a\1href="http://www.google.com/search?q=\2+site:{}"\3>'),)

# TODO: how to include blog or site variables? when do we do the replace?


def t(string_to_transform, site):

    for r, repl in transformations:
        string_to_transform = re.sub(r, repl.format(site), string_to_transform)

    return string_to_transform


def transform(*args, **kwargs):  # @UnusedVariable

    if args[1].page is not None:
        if args[1].page.text is not None:

            # TODO: use generic "tags" replacement, not site alone
            site = args[1].page.blog.site.url

            pagebreak = args[1].page.blog.kv('PageBreak').value

            text = args[1].page.text

            paginated_text = text.split(pagebreak)
            text_modified = [t(txt, site) for txt in paginated_text]
            args[1].page.text = pagebreak.join(text_modified)

    return args, kwargs
