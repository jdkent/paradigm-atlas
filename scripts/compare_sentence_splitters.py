"""Compare sentence splitters (regex, pySBD, spaCy en_core_web_sm) on tricky cases + real passages."""
import json, re, time, sys, warnings, random
warnings.filterwarnings("ignore")
sys.path.insert(0, '.')
import pysbd, spacy
from taskcat.sentence_schema import _SPLIT
seg = pysbd.Segmenter(language="en", clean=False, char_span=True)
nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "attribute_ruler", "tagger"])
nlp.max_length = 2_000_000
def s_regex(t): return [p for p in _SPLIT.split(t) if p.strip()]
def s_pysbd(t): return [x.sent.strip() for x in seg.segment(t) if x.sent.strip()]
def s_spacy(t): return [s.text.strip() for s in nlp(t).sents if s.text.strip()]
SPL = {"regex": s_regex, "pysbd": s_pysbd, "spacy": s_spacy}
TRICKY = [
 "Stimuli were adapted from Knutson et al. (2001). Participants pressed a button.",
 "Responses were faster for congruent trials (see Fig. 2). Accuracy was high.",
 "Each trial lasted approx. 2.5 s, i.e. 30 trials per run. The ISI was 1.5 s.",
 "Faces vs. houses were contrasted (e.g. Haxby et al. 2001). Results are in Table 3.",
 "Participants (N = 24; M age = 21.3 yrs., SD = 2.1) were tested. They gave consent.",
 "The task (cf. Exp. 1) used 3 vs. 4 items. No feedback was given.",
]
GOLD_N = [2, 2, 2, 2, 2, 2]
ABBR = re.compile(r"\b(et al|Fig|Figs|e\.g|i\.e|vs|approx|ca|cf|Exp|No|resp|Eq|Tab|yrs|ms|min|sec|St|Dr|Inc|Ltd)\.$")
for name, f in SPL.items():
    ok = sum(len(f(t)) == n for t, n in zip(TRICKY, GOLD_N))
    print(f"{name:6s} tricky cases correct: {ok}/{len(TRICKY)}")
    for t in TRICKY[:0]: print(f(t))
rows = [json.loads(l) for l in open('data/passages_psych.jsonl')][:100] + [json.loads(l) for l in open('data/passages_train.jsonl')][:100]
random.seed(0)
for name, f in SPL.items():
    t0 = time.time(); n = bad = missed = lower_start = 0
    for r in rows:
        for line in r['passage'].split('\n'):
            if not line.strip(): continue
            ss = f(line)
            n += len(ss)
            for i, s in enumerate(ss):
                if ABBR.search(s) and i < len(ss) - 1: bad += 1
                if i > 0 and s[:1].islower(): lower_start += 1
                missed += len(re.findall(r"[a-z]{3,}\. (?=[A-Z][a-z]{2,} )", s))
    print(f"{name:6s} sentences {n:6d}  abbreviation-splits {bad:4d}  lowercase-starts {lower_start:4d}  internal-boundaries(missed) {missed:4d}  time {time.time()-t0:.1f}s")
