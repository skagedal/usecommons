# Standard Python libraries
import urllib, urllib2, os.path, json, re
from distutils.dir_util import mkpath

# Third party libraries
from wikitools import wiki, page, category
from bs4 import BeautifulSoup

# Own libraries
import stockphoto

USER_AGENT = 'CommonsCredits/0.1; http://github.com/skagedal/commons-credits/'

RE_LICENSE_CATEGORIES = [
    (re.compile('Category:' + _re), txt) 
    for (_re, txt) in
    (r'CC[\- _]BY-SA.*', 'CC-BY-SA'),
    (r'CC[\- _]BY.*', 'CC-BY'),
    (r'CC[\- _]Zero.*', 'CC0'),
    (r'GFDL.*', 'GNU Free Documentation License'),
    (r'PD[\- _]Old.*', 'Public Domain'),
    (r'PD[\- _]self.*', 'Public Domain'),
    (r'PD[\- _]author.*', 'Public Domain'),
    (r'PD.*', 'Public Domain'),
    (r'FAL', 'Art Libre - Free Art'),
    (r'Images requiring attribution', 'Attribution'),
    (r'Copyrighted free use.*', 'Copyrighted Free Use'),
    (r'Mozilla Public License', 'Mozilla Public License'),
    (r'GPL', 'GNU General Public License'),
    (r'LGPL', 'GNU Lesser General Public License'),
    (r'Free screenshot.*', 'Free screenshot')
]

def _contents_html(tag):
    return "".join(map(unicode, tag.contents))

class Credits:
    def __init__(self, title, url, html, categories):
        self.title = title
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(html)
        self.categories = categories
    
    def get_td_soup(self, id):
        td1 = self.soup.find(id = id)
        if not td1 is None:
            return td1.find_next_sibling('td')
        return None

    def get_entry(self, id):
        td = self.get_td_soup(id)
        return _contents_html(td) if td else None

    def description(self):
        return self.get_entry('fileinfotpl_desc') or ""

    def date(self):
        return self.get_entry('fileinfotpl_date') or ""

    def raw_author(self):
        return self.get_entry('fileinfotpl_aut') or ""

    def author(self):
        td = self.get_td_soup('fileinfotpl_aut')
        if td is None:
            return ""
        # Check for use of {{Creator}} template
        creator = td.find(id = 'creator')
        if creator is not None:
            return _contents_html(creator)
        else:
            return _contents_html(td)
        
    def source(self):
        return self.get_entry('fileinfotpl_src') or ""

    def permission(self):
        return self.get_entry('fileinfotpl_perm') or ""

    def licenses(self):
        licenses = []
        for cat in self.categories:
            for (re_, txt) in RE_LICENSE_CATEGORIES:
                if (re_.match(cat)):
                    licenses += [txt]
        return licenses


    def explicit_credit_line(self):
        pass

    def commonslink(self, text):
        return '<a href="%s">%s</a>' % (self.url, text)

    def credit_line(self):
        # Explicit credit line if there is one, otherwise build one
        return self.author() + " / " + ", ".join(self.licenses()) + " " + \
            self.commonslink("(Wikimedia Commons)")

    def attribution(self):
        return stockphoto.get_attribution_text(self.html, self.url, True)

class Cache:
    """Provides caching. Currently caches forever."""
    def __init__(self, dir):
        self.dir = dir
        mkpath(dir)

    def get(self, id, fun, use_json):
        """Memoize the return value of `fun`. Save in a file recognized
        by `id`.  If `use_json`, save as JSON, otherwise, as raw string."""
        filepath = os.path.join(self.dir, urllib.quote(id, ''))
        if os.path.isfile(filepath):
            fp = open(filepath, 'r')
            if (use_json):
                return json.load(fp)
            else:
                return fp.read()
        else:
            content = fun()
            fp = open(filepath, 'w')
            if (use_json):
                json.dump(content, fp)
            else:
                fp.write(content)
            return content

class Commons:
    def __init__(self, base_url = 'http://commons.wikimedia.org'):
        self.base_url = base_url
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

    def getCredits(self, title):
        """`title` is a full wiki title like 'File:Fuji_apple.jpg'"""
        def _getcats():
            return page.Page(self.site(), title).getCategories()
        def _gethtml():
            return self.getHTML(title)

        cache = Cache(dir = 'cache')
        return Credits(title, 
                       self.base_url + '/wiki/' + title,
                       cache.get(title + '.txt', _gethtml, False),
                       cache.get(title + '.cats', _getcats, True))


if __name__ == "__main__":
    title = 'File:Fuji_apple.jpg'
    commons = Commons()
    credits = commons.getCredits(title)
    print (credits.categories)
    print (len(credits.html))
    print (credits.author())
    print (credits.permission())

    
