import urllib, urllib2
from wikitools import wiki, api, page
from distutils.dir_util import mkpath
import os.path, json

USER_AGENT = 'CommonsCredits/0.1; http://github.com/skagedal/commons-credits/'

class Credits:
    def __init__(self, html, categories):
        self.html = html
        self.categories = categories

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
            self._site = wiki.Wiki(base_url + '/w/api.php')
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
        return Credits(cache.get(title + '.txt', _gethtml, False),
                       cache.get(title + '.cats', _getcats, True))


if __name__ == "__main__":
    title = 'File:Fuji_apple.jpg'
    commons = Commons()
    credits = commons.getCredits(title)
    print (credits.categories)
    print (len(credits.html))
