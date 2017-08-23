import re

minifications = (
    (re.compile(r'\&nbsp;', re.M), r' '),
    (re.compile(r'\n', re.M), r' '),
    (re.compile(r'\s{2,}', re.M), r' '),
    (re.compile(r'\t', re.M), r''),
    (re.compile(r'>\s(<[^>]*?>)\s(\S)', re.M), r'>\1 \2'),
    )

def minify(file_text, blog_path, file_path):

    for rgx, rpl in minifications:
        file_text = re.sub(rgx, rpl, file_text)

    return (file_text, blog_path, file_path), {}
