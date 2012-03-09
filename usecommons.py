# coding=utf-8
# Copyright (c) 2010-2011  Magnus Manske
#           (c) 2011-2012  Krinkle
#           (c) 2012-      Simon Kågedal Reimer
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#    This code is based on the MediaWiki "StockPhoto" gadget, written
#    by Magnus Manske and Krinkle, converted to Python by Simon
#    Kågedal Reimer.  Magnus and Krinkle agreed to license their code
#    under the above MIT/X11 license: http://j.mp/stockphoto-license  
#    License text from: http://copyfree.org/licenses/mit/license.txt

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

USER_AGENT = 'usecommons/0.1.0; http://skagedal.github.com/usecommons/'

def _next_td(soup, id):
    # Find the next <td> element that is a sibling of the element
    # with the given `id`.
    tag = soup.find(id = id)
    if tag is not None:
        return tag.findNextSibling('td')
    return None

class Field:
    def __init__(self, tag):
        self.tag = tag

    def exists(self):
        return self.tag is not None

    def text(self):
        # Get contents as pure text.
        if self.tag is None:
            return ""
        return self.tag.getText()
        
    def html(self):
    # Get contents as html. 
        if self.tag is None:
            return ""
        if BEAUTIFULSOUP_VERSION == 3:
            return self.tag.renderContents()
        else:
            # There is no renderContents in bs4?
            return "".join(map(unicode, self.tag.contents))


    def contents(self, use_html):
        return self.html() if use_html else self.text()

class License:
    """Class for storing license information."""
    def __init__(self, tag):
        """Constructor. Call with a BeautifulSoup tag of the element
        with class .licensetpl"""
        self.tag = tag
        self.link = Field(tag.find(True, 'licensetpl_link'))
        self.short = Field(tag.find(True, 'licensetpl_short'))
        self.long = Field(tag.find(True, 'licensetpl_long'))
        self.attr = Field(tag.find(True, 'licensetpl_attr'))
        self.aut = Field(tag.find(True, 'licensetpl_aut'))
        self.link_req = Field(tag.find(True, 'licensetpl_link_req'))
        self.attr_req = Field(tag.find(True, 'licensetpl_attr_req'))

    def url(self):
        if self.link.exists():
            url = self.link.html()
            if not '//' in url:
                return "http://" + url
            else:
                return url
        else:
            return ""

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

			


class Credits:
    def __init__(self, title, url, html, categories):
        self.title = title
        self.url = url
        self.html = html
        self.soup = BeautifulSoup(html)
        self.categories = categories 

        # "Raw" fields
        td_field = lambda s: Field(_next_td(self.soup, s))
        self.fileinfotpl_aut = td_field("fileinfotpl_aut")
        self.fileinfotpl_src = td_field("fileinfotpl_src")
        self.fileinfotpl_credit = td_field("fileinfotpl_credit")
        self.fileinfotpl_desc = td_field("fileinfotpl_desc")
        self.fileinfotpl_date = td_field("fileinfotpl_date")
        self.fileinfotpl_perm = td_field("fileinfotpl_perm")
        self.own_work = Field(self.soup.find(id = "own_work"))
        self.creator = Field(self.soup.find(id = "creator"))

        self.licenses = [License(tag) 
                         for tag in self.soup.findAll(True, "licensetpl")]


        self.licenses = [x for x in self.licenses if x.short.html() != ""]
    
    def commonslink(self, use_html):
        fromtext = "from Wikimedia Commons"
        if use_html:
            return ', <a href="%s">%s</a>' % (self.url, fromtext)
        else:
            return fromtext


    def use_from_commons(self):
        # Should retrn true if author field contains "Original uploader was"
        # or self.own_work.exists()
        return True



    def author_attribution_text(self, use_html):
        author = self.fileinfotpl_aut.text().strip()
        source = self.fileinfotpl_src.text().strip()
    
        # Remove boiler template; not elegant, but...
        if "This file is lacking author information" in author:
            author = ""
        if re.match(r"[Uu]nknown$", author):
            author = ""

        re_ = re.compile(r"\s*\(talk\)", flags=re.IGNORECASE)
        author = re_.sub("", author)

        if "Original uploader was" in author:
            author = re.sub(r"\s*Original uploader was\s*", "", author)

        # Remove boiler template; not elegant, but...
        if "This file is lacking source information" in source:
            source = ""

        if author != "" and self.own_work.exists(): 
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

        if self.creator.exists():
             attribution = self.creator.text()

        if len(self.licenses) > 0 and self.licenses[0].aut.exists():
            attribution = self.licenses[0].aut.content(use_html)

        if len(self.licenses) > 0 and self.licenses[0].attr.exists():
            attribution = self.licenses[0].attr.content(use_html)

        return attribution        

    def license_text(self, use_html):
        attribution_required = True
        gfdl_note = False

        if len(self.licenses) == 0:
            # i18n.see_page_for_license
            return "[" + "see page for license" + "]";

        for license in self.licenses:
            if license.attr_req == "false":
                attribution_required = False
            if "GFDL" in license.short.html():
                gfdl_note = True
            if use_html and license.link.exists():
                license.text = '<a href="' + license.url() + '">' + \
                    license.short.html() + '</a>'
            else:
                if license.link_req.html() == "true":
                    license.text = "%s (%s)" % (license.short.html(), 
                                                license.url())
                else:
                    license.text = license.short.html()

        texts = [l.text for l in self.licenses]
        if len(texts) > 1:
            return " [" + texts[0] + " or " + ", ".join(texts[1:]) + "]"

        return " [" + ", ".join(texts) + "]"

    def attribution(self, use_html = True):
        """Return a complete attribution line including license."""

        if self.fileinfotpl_credit.exists():
            text = self.fileinfotpl_credit.content(use_html)
        else:
            text = self.author_attribution_text(use_html) + \
                   self.license_text(use_html)

        return text + self.commonslink(use_html)

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
