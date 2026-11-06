"""License-checked Europe PMC full-text XML retrieval for local evidence indexing.

This path is allowlisted to one public scientific repository and one article
at a time. Only document bodies with a supported machine-readable open
license are indexed; everything else is refused, not guessed or scraped.
"""
from hashlib import sha256
from urllib.request import Request, urlopen
from xml.etree import ElementTree
import re

from .knowledge_index import upsert_paper

PMCID = re.compile(r"^PMC[0-9]{4,12}$")
MAX_XML_BYTES = 650_000
LICENSE_URLS = {
    "creativecommons.org/licenses/by/4.0": "CC-BY-4.0",
    "creativecommons.org/licenses/by/3.0": "CC-BY-3.0",
    "creativecommons.org/licenses/by-sa/4.0": "CC-BY-SA-4.0",
    "creativecommons.org/publicdomain/zero/1.0": "CC0-1.0",
}


def fulltext_url(pmcid):
    if not isinstance(pmcid, str) or not PMCID.fullmatch(pmcid):
        raise ValueError("Requires a valid public PMC identifier, e.g. PMC3258128")
    return f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def download_xml(pmcid, opener=urlopen):
    req = Request(fulltext_url(pmcid), headers={
        "User-Agent": "PlenumScientificIntelligence/1.2 open-license-evidence",
        "Accept": "application/xml",
    })
    with opener(req, timeout=20) as resp:
        data = resp.read(MAX_XML_BYTES + 1)
    if len(data) > MAX_XML_BYTES:
        raise ValueError("Scientific document exceeds bounded retrieval size")
    return data


def _plain_text(element):
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def parse_open_article(pmcid, data):
    if not PMCID.fullmatch(pmcid):
        raise ValueError("Invalid PMC identifier")
    if not isinstance(data, bytes) or len(data) > MAX_XML_BYTES:
        raise ValueError("Invalid XML bytes")
    lower = data.lower()
    if b"<!doctype" in lower or b"<!entity" in lower:
        raise ValueError("External/expanded XML entities are not accepted")
    root = ElementTree.fromstring(data)
    if root.tag != "article":
        raise ValueError("Expected an article-level JATS XML document")
    licenses = root.findall(".//license")
    approved = None
    # JATS publishers vary: CC links may occur in license attributes,
    # nested <ext-link> elements, or plain-text <license-p>.
    # Accept only exact recognized CC license URLs, not broad CC wording.
    allowed_uri = {scheme + "://" + url: name
                   for url, name in LICENSE_URLS.items()
                   for scheme in ("http", "https")}
    for license_tag in licenses:
        candidates = []
        for node in license_tag.iter():
            candidates.extend(v for k, v in node.attrib.items()
                              if k.endswith("href"))
            candidates.extend(re.findall(
                r"https?://creativecommons\\.org/(?:licenses|publicdomain)/[A-Za-z0-9/.-]+",
                node.text or "", flags=re.I))
        for candidate in candidates:
            value = candidate.lower().split("#", 1)[0].split("?", 1)[0].rstrip("/").rstrip(".")
            if value in allowed_uri:
                approved = allowed_uri[value]
                break
        if approved:
            break
    if approved is None:
        raise ValueError("No approved open license URI in JATS document")
    title = _plain_text(root.find(".//article-title"))
    if len(title) < 2:
        raise ValueError("Missing scientific title")
    paragraphs = []
    for element in root.findall(".//abstract//p") + root.findall(".//body//p"):
        content = _plain_text(element)
        if len(content) > 25:
            paragraphs.append(content)
    if not paragraphs:
        raise ValueError("No extractable substantive abstract/body text")
    excerpt = "\n".join(paragraphs)
    # Bounded local indexing avoids an unbounded copy of articles.
    excerpt = excerpt[:30_000]
    doi = ""
    for ident in root.findall(".//article-id"):
        if ident.get("pub-id-type") == "doi":
            doi = _plain_text(ident)[:160]
            break
    return {
        "paper": {
            "source": "europepmc-open-access", "id": pmcid, "title": title,
            "url": f"https://europepmc.org/articles/{pmcid}",
            "doi": ("https://doi.org/" + doi) if doi else "",
            "license": approved,
        },
        "text": excerpt,
        "original_xml_sha256": sha256(data).hexdigest(),
        "full_article_included": False,
        "license_confirmed_from_article_xml": True,
    }


def index_open_article(db_path, pmcid, opener=urlopen):
    data = download_xml(pmcid, opener=opener)
    parsed = parse_open_article(pmcid, data)
    result = upsert_paper(db_path, parsed["paper"], fulltext=parsed["text"])
    return {
        "pmcid": pmcid, "indexed": result["fulltext_indexed"],
        "title": parsed["paper"]["title"], "url": parsed["paper"]["url"],
        "license": result["license"],
        "xml_sha256": parsed["original_xml_sha256"],
        "indexed_excerpt_characters": len(parsed["text"]),
        "full_article_archived": False,
        "scientific_claims_verified": False,
    }
