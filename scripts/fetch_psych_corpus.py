"""Sample open-access behavioral psychology papers (non-neuroimaging) from Europe PMC; save JATS + text + bib.
Usage: fetch_psych_corpus.py OUTDIR N_PER_JOURNAL"""
import json, os, sys, random, time
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from taskcat.jats_text import jats_to_text
from taskcat.bibliography import parse_jats
OUT = sys.argv[1]; NPJ = int(sys.argv[2]); os.makedirs(OUT, exist_ok=True)
JOURNALS = ["Psychon Bull Rev", "J Exp Psychol Gen", "J Exp Psychol Learn Mem Cogn", "J Exp Psychol Hum Percept Perform",
            "Cognition", "Mem Cognit", "Atten Percept Psychophys", "Psychol Sci", "Front Psychol", "PLoS One",
            "R Soc Open Sci", "J Cogn", "Q J Exp Psychol (Hove)", "Behav Res Methods", "Cogn Emot", "Emotion",
            "Dev Sci", "J Exp Child Psychol", "Psychol Res", "Exp Brain Res", "J Vis", "Learn Mem", "Collabra Psychol",
            "Cogn Res Princ Implic", "Acta Psychol (Amst)", "Conscious Cogn", "Neuropsychologia", "Cortex",
            "J Neurophysiol", "Sci Rep", "eLife", "Nat Hum Behav", "Open Mind (Camb)", "Comput Brain Behav",
            "Judgm Decis Mak", "J Abnorm Psychol", "Behav Res Ther", "J Anxiety Disord", "Appetite", "Pain"]
S = requests.Session()
def search(j, n):
    q = (f'JOURNAL:"{j}" AND OPEN_ACCESS:y AND HAS_FT:y AND PUB_YEAR:[2008 TO 2025] AND '
         f'(METHODS:"participants" AND (METHODS:"trial" OR METHODS:"task" OR METHODS:"stimuli")) '
         f'NOT (METHODS:"fMRI" OR METHODS:"magnetic resonance" OR METHODS:"PET" OR ABSTRACT:"meta-analysis" OR '
         f'ABSTRACT:"systematic review" OR ABSTRACT:"mice" OR ABSTRACT:"rats")')
    r = S.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
              params={"query": q, "format": "json", "pageSize": 1000, "resultType": "lite"}, timeout=60)
    res = r.json().get("resultList", {}).get("result", [])
    random.Random(hash(j) % 1000).shuffle(res)
    return [x for x in res if x.get("pmcid")][:n]
man = []
for j in JOURNALS:
    try:
        hits = search(j, NPJ)
    except Exception as e:
        print("search fail", j, e); continue
    for h in hits:
        pmc = h["pmcid"]; d = os.path.join(OUT, pmc)
        if os.path.exists(os.path.join(d, "text.txt")):
            man.append({"dbid": pmc, "pmid": h.get("pmid"), "pmcid": pmc, "doi": h.get("doi"), "title": h.get("title"),
                        "journal": j, "year": h.get("pubYear"), "authors": h.get("authorString")}); continue
        try:
            x = S.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML", timeout=60)
            if x.status_code != 200 or b"<body" not in x.content: continue
        except Exception:
            continue
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "article.xml"), "wb").write(x.content)
        open(os.path.join(d, "text.txt"), "w").write(jats_to_text(x.content))
        try:
            json.dump(parse_jats(os.path.join(d, "article.xml")), open(os.path.join(d, "bib.json"), "w"))
        except Exception:
            pass
        man.append({"dbid": pmc, "pmid": h.get("pmid"), "pmcid": pmc, "doi": h.get("doi"), "title": h.get("title"),
                    "journal": j, "year": h.get("pubYear"), "authors": h.get("authorString")})
    print(j, len(hits), len(man), time.strftime("%H:%M:%S"), flush=True)
with open(os.path.join(OUT, "manifest.jsonl"), "w") as f:
    for m in man: f.write(json.dumps(m) + "\n")
