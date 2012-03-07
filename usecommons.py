# Standard Python libraries
import sys, urllib, urllib2, os.path, json, re
from distutils.dir_util import mkpath

# Third party libraries
HAVE_WIKITOOLS = True
try:
    from wikitools import wiki, page, category
except ImportError:
    HAVE_WIKITOOLS = False
try:
    from bs4 import BeautifulSoup
    HAVE_BEAUTIFULSOUP = True
    BEAUTIFULSOUP_VERSION = 4
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup
        HAVE_BEAUTIFULSOUP = True
        BEAUTIFULSOUP_VERSION = 3
    except ImportError:
        sys.stderr.write("Please install Beautiful Soup.")
        sys.exit(1)

USER_AGENT = 'CommonsCredits/0.1; http://github.com/skagedal/commons-credits/'

def _next_td(soup, id):
    # Find the next <td> element that is a sibling of the element
    # with the given `id`.
    tag = soup.find(id = id)
    if tag is not None:
        return tag.findNextSibling('td')
    return None

def _text(tag):
    # Get contents of tag as pure text.
    if tag is None:
        return ""
    return tag.getText()

def _html(tag):
    # Get contents of tag as html. 
    if tag is None:
        return ""
    if BEAUTIFULSOUP_VERSION == 3:
        return tag.renderContents()
    else:
        # There is no renderContents in bs4?
        return "".join(map(unicode, tag.contents))

class License:
    """Class for storing license information."""
    def __init__(self, tag):
        """Constructor. Call with a BeautifulSoup tag of the element
        with class .licensetpl"""
        self.tag = tag
        self.link = tag.find(True, 'licensetpl_link')
        self.short = tag.find(True, 'licensetpl_short')
        self.long = tag.find(True, 'licensetpl_long')
        self.attr = tag.find(True, 'licensetpl_attr')
        self.aut = tag.find(True, 'licensetpl_aut')
        self.link_req = tag.find(True, 'licensetpl_link_req')
        self.attr_req = tag.find(True, 'licensetpl_attr_req')

class Fields:
    """Class for storing fields scraped from HTML."""
    def __init__(self, soup):
        self.soup = soup
        self.fileinfotpl_aut = _next_td(soup, "fileinfotpl_aut")
        self.fileinfotpl_src = _next_td(soup, "fileinfotpl_src")
        self.fileinfotpl_credit = _next_td(soup, "fileinfotpl_credit")
        self.fileinfotpl_desc = _next_td(soup, "fileinfotpl_desc")
        self.fileinfotpl_date = _next_td(soup, "fileinfotpl_date")
        self.fileinfotpl_perm = _next_td(soup, "fileinfotpl_perm")
        self.own_work = soup.find(id = "own_work")
        self.creator = soup.find(id = "creator")

        self.licenses = [License(tag) 
                         for tag in soup.findAll(True, "licensetpl")]


        self.licenses = [x for x in self.licenses if _html(x.short) != ""]

# Short JavaScript/jQuery to Python/Beautiful Soup guide:
#   $.trim(string) --> 
#       string.strip() 
#   string.match(regexp) --> 
#       re.search(pattern, string, flags)
#   string.match(/^pattern/) --> 
#       re.match(pattern, string, flags)
#   string.replace(/pattern/, repl) --> 
#       re.compile(pattern, flags).sub(repl, string, count = 1)
#   string.replace(/pattern/g, repl) --> 
#       re.compile(pattern, flags).sub(repl, string)
#   (re.sub doesn't allow flags in Python versions < 2.7)

def get_author_attribution(fields, use_html):
    fromCommons = False
    content = _html if use_html else _text

    author = _text(fields.fileinfotpl_aut).strip()
    source = _text(fields.fileinfotpl_src).strip()
    
    # Remove boiler template; not elegant, but...
    if "This file is lacking author information" in author:
        author = ""
    if re.match(r"[Uu]nknown$", author):
        author = ""

    # author = re.sub(r"\s*\(talk\)", "", author, flags=re.IGNORECASE)
    author = re.compile(r"\s*\(talk\)", flags=re.IGNORECASE).sub("", author)

    if "Original uploader was" in author:
        author = re.sub(r"\s*Original uploader was\s*", "", author)
        fromCommons = True

    # Remove boiler template; not elegant, but...
    if "This file is lacking source information" in source:
        source = ""

    if author != "" and fields.own_work is not None: 
         # Remove "own work" notice
         source = ""
         fromCommons = True;

    if author != "" and len(source) > 50:
         # Remove long source info
         source = ""

    # \u25BC == &#9660; == BLACK DOWN-POINTING TRIANGLE
    if author.startswith(u"[\u25BC]"):
         author = author[:3]
         author = author.split("Description")[0].strip()

    attribution = author
    if source != "":
         if attribution != "":
              attribution += " (%s)" % source
         else:
              attribution = source

    return_author = attribution # might not need

    if author != "":
         # i18n.by_u
         attribution = "By" + " " + attribution
    else:
         # i18n.see_page_for_author
         attribution = "See page for author"

    if fields.creator is not None:
         attribution = _text(fields.creator)

    if len(fields.licenses) > 0 and fields.licenses[0].aut is not None:
        attribution = content(fields.licenses[0].aut)

    if len(fields.licenses) > 0 and fields.licenses[0].attr is not None:
        attribution = content(fields.license[0].attr)

    if fields.fileinfotpl_credit is not None:
        attribution = content(fields.fileinfotpl_credit)

    return attribution
			
def get_license(fields, use_html):
    attribution_required = True
    gfdl_note = False

    if len(fields.licenses) == 0:
        # i18n.see_page_for_license
        return "[" + "see page for license" + "]";
    
    for license in fields.licenses:
        if license.attr_req == "false":
            attribution_required = False
        if "GFDL" in _html(license.short):
            gfdl_note = True
        if use_html and license.link is not None:
            license.text = '<a href="' + _html(license.link) + '">' + \
                _html(license.short) + '</a>'
        else:
	    if _html(license.link_req) == "true":
                license.text = "%s (%s)" % (_html(license.short), link)
            else:
                license.text = _html(license.short)

    texts = [l.text for l in fields.licenses]
    if len(texts) > 1:
        return " [" + texts[0] + " or " + ", ".join(texts[1:]) + "]"

    return " [" + ", ".join(texts) + "]"

def get_attribution_text(html, url, use_html):
    text = ""
    soup = BeautifulSoup(html)
    fields = Fields(soup)
   
    license = get_license(fields, use_html)
    attribution = get_author_attribution(fields, use_html)

    # from = stockPhoto.fromCommons ? stockPhoto.i18n.from_wikimedia_commons : stockPhoto.i18n.via_wikimedia_commons;
    fromtext = "from Wikimedia Commons"

    if fields.fileinfotpl_credit is not None:
        text = attribution
    else:
        text = attribution + license

    if use_html:
        text += ', <a href="' + url + '">' + fromtext + "</a>"
    else:
        text += fromtext

    return text

class Credits:
    def __init__(self, title, url, html, categories):
        self.title = title
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(html)
        self.categories = categories
    
    def commonslink(self, text):
        return '<a href="%s">%s</a>' % (self.url, text)

    def attribution(self):
        return get_attribution_text(self.html, self.url, True)

class Cache:
    """Provides caching. Currently caches forever."""
    def __init__(self, dir):
        self.dir = dir
        mkpath(dir)

    def get(self, id, fun, use_json):
        """Memoize the return value of `fun`. Save in a file recognized
        by `id`.  If `use_json`, save as JSON, otherwise, as raw string."""
        filepath = os.path.join(self.dir, urllib.quote(id, ''))
        
        try:
            fp = open(filepath, 'r')
            if use_json:
                return json.load(fp)
            else:
                return fp.read()
        except IOError:
            content = fun()
            try:
                fp = open(filepath, 'w')
                if use_json:
                    json.dump(content, fp)
                else:
                    fp.write(content)
            except IOError:
                pass #logging.lo
            return content

class Commons:
    def __init__(self, 
                 base_url = 'http://commons.wikimedia.org',
                 cache_dir = "cache"):
        self.base_url = base_url
        self.cache_dir = cache_dir
        self._site = None
        self.url_opener = urllib2.build_opener()
        self.url_opener.addheaders = [('User-agent', USER_AGENT)]

    def site(self):
        if self._site is None:
            self._site = wiki.Wiki(self.base_url + '/w/api.php')
        return self._site

    def getHTML(self, title):
        url = self.base_url + '/w/index.php?action=render&title=' + title
        return self.url_opener.open(url).read()

    def get(self, title):
        """`title` is a full wiki title like 'File:Fuji_apple.jpg'"""
        def _getcats():
            return page.Page(self.site(), title).getCategories()
        def _gethtml():
            return self.getHTML(title)

        cache = Cache(dir = self.cache_dir)
        html = cache.get(title + '.txt', _gethtml, False)
        if HAVE_WIKITOOLS:
            cats = cache.get(title + '.cats', _getcats, True)
        else:
            cats = None
        return Credits(title, self.base_url + '/wiki/' + title, html, cats)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(Commons().get(u'File:' + sys.argv[1]).attribution())
    else:
        print(u"""usage: 
python usecommons.py <filename>
  where <filename> is a Commons page title for a file, without the 
  namespace prefix. E.g.: python usecommons.py Fuji_apple.jpg""")
