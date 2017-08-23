# Default date format for blog posts
def date(string):
	return string.strftime('%B %-d, %Y')

from core.models import Media,Tag,Page

# Get patreon bug for article
def patreon(n):
	if '@patreon' in n.tags_list:
		patreon = "<img src='/media/patreon.png' style='height:24px' alt='Patreon' title='This article was made possible by the generous sponsorship of our Patreon supporters.'/> "
	else:
		patreon = ""
	return patreon


# Placeholder image for blog posts
def placeholder():
	return Media.get(Media.friendly_name.contains('anime-3.jpg'))

# Article image object, returns image with associated attributes
def article_img(article):
	# Eventually we'll replace all this with just img and placeholder
	# since LegacyHeaderImage will be phased out
	try:
		image = Media.load(article.kv_get('img').get().value)
	except:
		try:
			article_image_id = article.kv_get('LegacyHeaderImage').get().value
			image_id = Media.kv_get('legacy_id',article_image_id).get().objectid
			image = Media.load(image_id)
		except:
			image= placeholder()
	
	try:
		image.copyright = image.kv_get('copyright').get().value
	except:
		image.copyright = None
	try:
		image.position = image.kv_get('position').get().value
	except:
		image.position = 50
	return image


def get_tag(tag_name):	
	articles = Tag.select().where(Tag.tag==tag_name).get().pages.order_by(
		Page.publication_date.desc())[:3]
	return articles

import re

replace=[
	['<a href=.search:([^\'"]*).[^>]*?>',
	r'<a target="_blank" href="https://google.com/search?q=\1%20site:ganriki.org">'],
	['<a href=.google:([^\'"]*).[^>]*?>',
	r'<a target="_blank" href="https://google.com/search?q=\1">'],
	['<a href=.amazon.com:([^\'"]*).[^>]*?>',r'<a href="https://www.amazon.com/dp/\1?tag=thegline">'],
    [r'\&nbsp;',' '],
    [r' -- ',' &mdash; '],
    #[r'([$ ,;])"',r'\1“'],
    #[r'"([\,\.\!\? ])',r'”\1'],
]

for n in replace:
	n[0]=re.compile(n[0])

re_excerpt = re.compile(r'<p class=.lead.[^>]*?>(.*?)</p>.*',re.DOTALL)
      
caption = re.compile('''<div class=['"]([^'"]*?)['"][^>]*?>[^<]*?<img [^>]*?src=["']([^'"]*?)['"][^>]*?>[^<]*?<img [^>]*?src=['"]([^'"]*?)['"][^>]*?>[^<]*?<p>(.*?)</p>[^<]*?</div>''',re.DOTALL)

single_caption = re.compile('''<div class=['"]([^'"]*?)['"][^>]*?>\s*?<img [^>]*?src=["']([^'"]*?)['"][^>]*?>\s*?<p>(.*?)</p>\s*?</div>''',re.DOTALL)

replacement = r'<figure class="\1"><a href="\2" data-toggle="lightbox"><img alt="\2" class="lazy" src="/media/gray.png" data-original="\2"/></a>&nbsp;<a href="\3" data-toggle="lightbox"><img alt="\3" class="lazy" src="/media/gray.png" data-original="\3"/></a><figcaption><span class="copyright">{}</span><br/>\4</figcaption></figure>'

single_replacement = r'<figure class="\1"><div class="c-fix"><span class="img-caption-sm disable-text">{}</span><a href="\2" data-toggle="lightbox"><img alt="\2" class="lazy" src="/media/gray.png" data-original="\2"/></a></div><figcaption>\3</figcaption></figure>'

amazon = re.compile(r'''<p>(.*?)<a href=['"](left|right).amazon.com:([^'"]*?)['"][^>]*?>(.*?)</a>(.*?)</p>''')

amazon_replacement = r'''
<div class="pclear-\2">
<div style="" class="well well-sm pull-\2 float-\2"><a title="Click here to purchase this item. Purchases support this site." target="_blank" rel="nofollow" href="http://www.amazon.com:/dp/\3/?tag=thegline"><img alt="Amazon \3" class="bx" src="http://images.amazon.com/images/P/\3.01._SS100_LZZZZZZZ.jpg"></a></div>
<p>\1<a href="http://www.amazon.com/dp/\3?tag=thegline">\4</a>\5</p></div>
'''

# Image caption regex
def captions(text):
    for cap,rep in ((single_caption,single_replacement),(caption,replacement)):
        poz=0
        while 1:
            match=cap.search(text,poz)
            if not match:
                break
            poz = match.start()+1
            img_obj = Media.select().where(Media.url==match.group(2)).get()
            try:
                img_copyright = img_obj.kv_get('copyright').get().value
            except:
                img_copyright = '[<i>No copyright information specified</i>]'
            text=cap.sub(rep.format(img_copyright),text,count=1)
    return text
      
# Generic replacement regex for Amazon links, etal.
def rep(str):
	for n in replace:
		str=n[0].sub(n[1],str)
	pos=0
	while 1:	
		match=amazon.search(str,pos)
		if not match:
			break
		pos=match.end()
		str=amazon.sub(amazon_replacement,str)
	return str

def rep_excerpt(str):
	return re_excerpt.sub(r'<p>\1</p>',str)
	

topic_footers={'@promo':'''
<div class="alert alert-info">
<b>Note:</b> This product was provided by the creator or publisher
as a promotional item for the sake of a review.
</div>
''',
'@purchased':'''
<div class="alert alert-info">
<b>Note:</b> The products mentioned here were purchased by the reviewer with personal
funds, or watched using the reviewer's personal streaming account.
No compensation was provided by the creators or publishers
for the sake of this review. 
</div>
'''}

topic_headers={
'@spoiler':'''
<div class="alert alert-danger">
<b>Warning:</b> This article contains <b>major spoilers.</b>
</div>
''',
'meta: Let\'s Film This':'''
<div data-header="meta-lets-film-this" class="alert alert-success">
<a href="/meta/lets-film-this"><b>Let's Film This</b></a> is an ongoing series where we explore the idea of adapting different anime as live-action productions: what it would take, which shows would make for the best adaptations, and what issues would be raised in the translation.
</div>
''',
'meta: Let\'s Animate This':'''
<div data-header="meta-lets-animate-this" class="alert alert-success">
<a href="/meta/lets-animate-this"><b>Let's Animate This</b></a> is an ongoing series where we explore the idea of adapting non-anime properties as anime productions: what it would take, which works would make for the best adaptations, and what issues would be raised in the translation.
</div>
''',
'meta: Short Takes':'''
<div data-header="meta-short-takes" class="alert alert-success">
<a href="/meta/short-takes"><b>Short Takes</b></a> looks at newly released products for ongoing titles, a way for us to examine a series in progress outside of a full-length critical piece.
</div>
'''}

author_blurb={'2':{'name':'Serdar Yegulalp',
'email':'serdar@ganriki.org',
'blurb':'''
<a href="mailto:serdar@ganriki.org">Serdar Yegulalp</a>
(<a href="https://twitter.com/genjipress">@genjipress</a>)
(<a href="https://plus.google.com/117543614012474733284" rel=author>G+</a>)
is Editor-in-Chief of Ganriki.org.
He has written about anime professionally as the Anime Guide for Anime.About.com, and as a contributor to Advanced Media Network, but has also been exploring the subject on his own since 1998.
'''},
'61':
{'name':'Jose San Mateo',
'email':'jsanmateo@gmail.com',
'blurb':'''
Jose is a straight-shooter of a geek, equipped with a voracious appetite for anime, video games, and comic books, and a mind compelled to bring it all together and tell you what it all means. He can be shouted at on Twitter as <a href="https://twitter.com/JAsanmateo">@JAsanmateo</a>.
'''}
}

default_author={1:author_blurb['2']}

class Author():
	def __init__(self,id):
		for n in author_blurb[id]:
			setattr(self,n,author_blurb[id][n])