"""Author keys from PubMed records: ORCID when present, else ascii(last)+first initial."""
import unicodedata, re

def _a(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()

def author_key(a):
    if a.get("orcid"):
        return "orcid:" + re.sub(r".*/", "", a["orcid"])
    last = re.sub(r"[^a-z]", "", _a(a.get("last")))
    ini = _a(a.get("initials") or a.get("fore") or "")[:1]
    return f"{last}_{ini}" if last else None

def name_key(a):
    """ORCID-independent key, to join ORCID and non-ORCID records of the same person."""
    last = re.sub(r"[^a-z]", "", _a(a.get("last")))
    ini = _a(a.get("initials") or a.get("fore") or "")[:1]
    return f"{last}_{ini}" if last else None
