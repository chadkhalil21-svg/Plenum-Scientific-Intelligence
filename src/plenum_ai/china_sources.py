"""Bounded public scientific signals from the Chinese Academy of Sciences
and China-affiliated OpenAlex papers. No subscription, scraping of gated pages,
national-security sources, institutional access or full-text mirroring.
"""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import re

CAS_BASE="https://english.cas.cn/newsroom/"
CAS_PATTERN=re.compile(r"^/newsroom/research-news/20[0-9]{4}/t20[0-9]{6}_[0-9]+\.shtml$")
CN_NOTE="At least one China-affiliated coauthor according to OpenAlex; not a claim of Chinese-only research."

class _CASParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active=None
        self.parts=[]
        self.articles=[]
    def handle_starttag(self,tag,attrs):
        if tag!="a":return
        href=dict(attrs).get("href","")
        url=urljoin(CAS_BASE,href)
        p=urlsplit(url)
        if p.scheme=="https" and p.hostname=="english.cas.cn" and CAS_PATTERN.fullmatch(p.path):
            self.active=url
            self.parts=[]
    def handle_data(self,data):
        if self.active is not None:
            self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.active:
            title=" ".join(" ".join(self.parts).split())[:330]
            if len(title)>6 and not any(x[1]==self.active for x in self.articles):
                date=re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{2}, 20[0-9]{2}",title)
                self.articles.append((title,self.active,date.group(0) if date else ""))
            self.active=None
            self.parts=[]

def cas_research_articles(data):
    if not isinstance(data,bytes) or len(data)>1_250_000:raise ValueError("CAS HTML exceeded limit")
    parser=_CASParser()
    parser.feed(data.decode("utf-8","replace"))
    # Do not fabricate a healthy feed if markup changes and no articles parse.
    if not parser.articles: raise ValueError("CAS research HTML schema changed or no links found")
    return parser.articles[:4]

def china_affiliated_works(data):
    import json
    if not isinstance(data,bytes) or len(data)>1_250_000:raise ValueError("OpenAlex result exceeded limit")
    payload=json.loads(data)
    if not isinstance(payload,dict) or not isinstance(payload.get("results"),list):
        raise ValueError("Unknown China-affiliated OpenAlex result schema")
    results=[]
    for work in payload["results"][:4]:
        if not isinstance(work,dict):continue
        authorships=work.get("authorships") or []
        has_china=any(isinstance(auth,dict) and any(
            isinstance(org,dict) and org.get("country_code")=="CN"
            for org in (auth.get("institutions") or []))
            for auth in authorships)
        if not has_china:continue
        title=work.get("title")
        doi=work.get("doi")
        ident=work.get("id")
        link=(doi if isinstance(doi,str) and doi.startswith("https://doi.org/10.")
              else ident if isinstance(ident,str) and re.fullmatch(
                  r"https://openalex.org/W[0-9]+",ident) else "")
        if isinstance(title,str) and len(title.strip())>=3 and link:
            results.append((title[:330],link,str(work.get("publication_date") or "")[:55]))
    return results
