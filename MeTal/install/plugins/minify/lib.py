import re

minifications = (
    (re.compile(r'\n', re.M), r' '),
    (re.compile(r'\s{2,}', re.M), r' '),
    (re.compile(r'\t', re.M), r''),
    (re.compile(r'> <', re.M), r'><'),)

def minify(text):

    n = text

    for rgx, rpl in minifications:
        n = re.sub(rgx, rpl, n)

    return n