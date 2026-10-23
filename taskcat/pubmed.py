"""NCBI E-utilities client (API key from /home/james/ns-pond-ingestion-workflow/.env: PUBMED_API_KEY, EMAIL).

- efetch_records(pmids): PubMed XML -> {pmid: {title, journal, year, authors[{last, fore, initials, orcid,
  affiliations}], mesh[], pub_types[], refs[pmid...]}}  (batches of 200; <=10 req/s with key)
- doi_to_pmid(doi), title_to_pmid(title, first_author, year): esearch lookups.
"""
import os, re, time, threading
import requests
from lxml import etree

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_lock = threading.Lock(); _last = [0.0]


def load_env(path="/home/james/ns-pond-ingestion-workflow/.env"):
    for line in open(path):
        m = re.match(r"\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$", line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))


def _get(endpoint, params, tries=5):
    params = {**params, "api_key": os.environ.get("PUBMED_API_KEY", ""), "email": os.environ.get("EMAIL", ""),
              "tool": "taskcat"}
    for a in range(tries):
        with _lock:  # global rate limit ~9 req/s
            wait = 0.11 - (time.time() - _last[0])
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            r = requests.post(f"{BASE}/{endpoint}", data=params, timeout=60)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(2 ** a)
    return None


def _t(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else None


def efetch_records(pmids):
    out = {}
    for i in range(0, len(pmids), 200):
        batch = pmids[i:i + 200]
        r = _get("efetch.fcgi", {"db": "pubmed", "id": ",".join(batch), "retmode": "xml"})
        if r is None:
            continue
        root = etree.fromstring(r.content, etree.XMLParser(recover=True, huge_tree=True))
        for art in root.iter("PubmedArticle"):
            pmid = _t(art.find(".//MedlineCitation/PMID"))
            a = art.find(".//Article")
            authors = []
            for au in art.iterfind(".//AuthorList/Author"):
                orcid = next((_t(x) for x in au.iterfind("Identifier") if x.get("Source") == "ORCID"), None)
                authors.append({"last": _t(au.find("LastName")), "fore": _t(au.find("ForeName")),
                                "initials": _t(au.find("Initials")), "collective": _t(au.find("CollectiveName")),
                                "orcid": orcid, "affiliations": [_t(x) for x in au.iterfind(".//AffiliationInfo/Affiliation")]})
            year = _t(art.find(".//JournalIssue/PubDate/Year")) or (_t(art.find(".//JournalIssue/PubDate/MedlineDate")) or "")[:4]
            refs = [_t(x) for x in art.iterfind(".//ReferenceList/Reference/ArticleIdList/ArticleId") if x.get("IdType") == "pubmed"]
            out[pmid] = {"title": _t(a.find("ArticleTitle")) if a is not None else None,
                         "journal": _t(art.find(".//Journal/Title")), "year": year or None, "authors": authors,
                         "mesh": [_t(x) for x in art.iterfind(".//MeshHeading/DescriptorName")],
                         "pub_types": [_t(x) for x in art.iterfind(".//PublicationType")], "refs": refs,
                         "abstract": " ".join(_t(x) or "" for x in art.iterfind(".//Abstract/AbstractText"))[:4000]}
    return out


def esearch(term):
    r = _get("esearch.fcgi", {"db": "pubmed", "term": term, "retmode": "json", "retmax": 5})
    if r is None:
        return []
    try:
        return r.json()["esearchresult"]["idlist"]
    except Exception:
        return []


def doi_to_pmid(doi):
    ids = esearch(f"{doi}[doi]")
    return ids[0] if len(ids) == 1 else None


def title_to_pmid(title, first_author=None, year=None):
    t = re.sub(r"[^\w\s-]", " ", title or "")
    t = " ".join(t.split()[:18])
    if len(t) < 15:
        return None
    term = f"{t}[ti]"
    if first_author:
        term += f" AND {first_author}[au]"
    ids = esearch(term)
    if len(ids) == 1:
        return ids[0]
    if year and len(ids) > 1:
        ids = esearch(term + f" AND {year}[dp]")
        return ids[0] if len(ids) == 1 else None
    return None
