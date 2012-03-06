def _next_td(soup, id):
    tag = soup.find(id = id)
    if tag is not None:
        return tag.find_next_sibling('td')
    return None

def _text(tag):
    return tag.toString()       # or something

def _html(tag):
    return "".join(map(unicode, tag.contents))

def _licensetpl_fields(tag):
     license = object()
     license.link = tag.find(True, 'licensetpl_link')
     license.short = tag.find(True, 'licensetpl_short')
     license.long = tag.find(True, 'licensetpl_long')
     license.attr = tag.find(True, 'licensetpl_attr')
     license.aut = tag.find(True, 'licensetpl_aut')
     license.link_req = tag.find(True, 'licensetpl_link_req')
     license.attr_req = tag.find(True, 'licensetpl_attr_req')
     return o

class Fields:
    def __init__(self, soup):
        self.soup = soup
        self.fileinfotpl_aut = _next_td(soup, "fileinfotpl_aut")
        self.fileinfotpl_src = _next_td(soup, "fileinfotpl_src")
        self.fileinfotpl_credit = _next_td(soup, "fileinfotpl_credit")

        self.own_work = soup.find(id = "own_work")
        self.creator = soup.find(id = "creator")

        self.licenses = [_licensetpl_fields(tag) 
                         for tag in soup.find_all(True, "licensetpl")]


        self.licenses = [x for x in self.licenses if x.short != ""]

# Short JavaScript/jQuery to Python/Beautiful Soup guide:
#   $.trim(string) --> string.strip() 
#   string.match(regexp) --> re.search(pattern, string, flags)
#   string.match(/^pattern/) --> re.match(pattern, string, flags)
#   string.replace(/pattern/, repl) --> re.sub(pattern, repl, string, count = 1, flags = flags)
#   string.replace(/pattern/g, repl) --> re.sub(pattern, repl, string, flags = flags)

def get_author_attribution(fields, use_html):
    fromCommons = False
    content = _html if use_html else _text

    author = _text(fields.fileinfotpl_aut).strip()
    source = _text(fields.fileinfotpl_src).strip()
    
    # Remove boiler template; not elegant, but...
    if re.search(r"This file is lacking author information", author):
        author = ""
    if re.match(r"[Uu]nknown$", author):
        author = ""

    author = re.sub(r"\s*\(talk\)", "", author, flags=re.IGNORECASE)

    if re.search(r"Original uploader was"):
        author = re.sub(r"\s*Original uploader was\s*", "", author)
        fromCommons = True

    # Remove boiler template; not elegant, but...
    if re.search(r"This file is lacking source information", source):
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

    if fields.license.aut is not None:
        attribution = content(fields.license.aut)

    if fields.license.attr is not None:
        attribution = content(fields.license.attr)

    if fields.fileinfotpl_credit is not None:
        attribution = content(fields.fileinfotpl_credit)

    return attribution
			
def get_license(soup, fields, use_html):
    attribution_required = True
    gfdl_note = False

    if len(fields.licenses) == 0:
        # i18n.see_page_for_license
        return "[" + "see page for license" + "]";
    
    for license in fields.licenses:
        if license.attr_req == "false":
            attribution_required = False
        if _has_substring(license.short, "GFDL"):
            gfdl_note = True
        if use_html and license.link is not None:
            license.text = '<a href="' + license.link + '">' + \
                license.short + '</a>'
        else:
	    if license.link_req == "true":
                license.text = "%s (%s)" % (license.short, link)
            else:
                license.text = license.short

    texts = [l.text for l in fields.licenses]
    if len(texts) > 1:
        return " [" + texts[0] + " or " + \
            texts[1:].join(", ") + "]"

    return " [" + texts.join(", ") + "]"

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

