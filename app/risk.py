"""Deterministic, explainable risk check for caller transcripts.

No ML here on purpose: every verdict comes with the categories and the exact
phrases that triggered them, so the family can see *why* a call was flagged.

Verdict rules:
  RED    if any credentials request, OR >= 2 categories, OR an unverified family
         claim + any pressure signal, OR a wrong code word (only if enabled)
  YELLOW if exactly 1 category, OR an unverified family claim with no pressure
         (family should call back on a number they already have)
  GREEN  if 0 categories and no unverified family claim
"""
import difflib
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

CONFIG = json.loads((Path(__file__).parent / "phrases.json").read_text(encoding="utf-8"))

GREEN, YELLOW, RED = "green", "yellow", "red"

# ---------------------------------------------------------------- normalization

_PUNCT = re.compile("[^\\w\\s\u0900-\u0DFF*]", re.UNICODE)   # keep all Indic scripts (incl. vowel signs)


def normalize(text: str) -> str:
    """Lowercase, NFC, drop Devanagari nukta, unify chandrabindu, strip punctuation."""
    t = unicodedata.normalize("NFC", text or "").lower()
    t = unicodedata.normalize("NFD", t).replace("़", "")  # nukta (ड़ -> ड, ज़ -> ज)
    t = unicodedata.normalize("NFC", t)
    t = t.replace("ँ", "ं")                          # chandrabindu -> anusvara
    t = t.replace("।", " ").replace("॥", " ")        # danda
    t = t.replace("‌", "").replace("‍", "")          # ZWNJ / ZWJ
    t = _PUNCT.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


# Rough Devanagari -> Roman transliteration (safety net for mixed-script output
# and for fuzzy code-word matching). Not linguistically perfect, by design.
_CONS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "f", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h",
}
_VOW = {"अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri", "ए": "e", "ऐ": "ai",
        "ओ": "o", "औ": "au", "ऑ": "o"}
_MATRA = {"ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri",
          "े": "e", "ै": "ai", "ो": "o", "ौ": "au", "ॉ": "o"}
_VIRAMA, _ANUSVARA, _VISARGA = "्", "ं", "ः"


def translit(text: str) -> str:
    out_words = []
    for word in text.split():
        if not re.search(r"[ऀ-ॿ]", word):
            out_words.append(word)
            continue
        s, i = [], 0
        while i < len(word):
            c = word[i]
            nxt = word[i + 1] if i + 1 < len(word) else ""
            if c in _CONS:
                s.append(_CONS[c])
                if nxt in _MATRA:
                    s.append(_MATRA[nxt]); i += 1
                elif nxt == _VIRAMA:
                    i += 1
                else:
                    s.append("a")
            elif c in _VOW:
                s.append(_VOW[c])
            elif c in (_ANUSVARA, _VISARGA):
                s.append("n" if c == _ANUSVARA else "h")
            elif c in _MATRA:
                s.append(_MATRA[c])
            else:
                s.append(c)
            i += 1
        w = "".join(s)
        if len(w) > 2 and w.endswith("a") and not w.endswith("aa"):
            w = w[:-1]  # schwa deletion at word end
        out_words.append(w)
    return " ".join(out_words)


def skeleton(roman: str) -> str:
    """Collapse common Hinglish spelling variation: aa->a, ee->i, oo->u, w->v, z->j."""
    s = roman.lower()
    for a, b in (("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u"), ("w", "v"),
                 ("z", "j"), ("ph", "f"), ("q", "k")):
        s = s.replace(a, b)
    s = re.sub(r"(?<=[aeiou])y(?=[aeiou])", "", s)  # jayegi -> jaegi
    return s


# ---------------------------------------------------------------- matching

def _phrase_regex(phrase: str) -> re.Pattern:
    p = normalize(phrase.replace("*", "STAR")).replace("star", "*")
    words = p.split()
    parts = [re.escape(w[:-1]) + r"\S*" if w.endswith("*") else re.escape(w) for w in words]
    return re.compile(r"(?:^|\s)" + r"\s+".join(parts) + r"(?=\s|$)")


_CACHE: Dict[str, re.Pattern] = {}


def _rx(phrase: str) -> re.Pattern:
    if phrase not in _CACHE:
        _CACHE[phrase] = _phrase_regex(phrase)
    return _CACHE[phrase]


def _is_roman(phrase: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9 *]+", phrase.lower()))


def find_phrases(norm_text: str, phrases: List[str], roman_view: Optional[str] = None) -> List[str]:
    """Return phrases (as written in config) found in the normalized text."""
    hits = []
    for ph in phrases:
        if _rx(ph).search(norm_text):
            hits.append(ph)
        elif roman_view is not None and _is_roman(ph) and len(ph.replace(" ", "")) >= 4:
            if _rx(skeleton(ph)).search(roman_view):
                hits.append(ph)
    return hits


def _remove(norm_text: str, phrases: List[str]) -> str:
    for ph in phrases:
        norm_text = _rx(ph).sub(" ", norm_text)
    return re.sub(r"\s+", " ", norm_text).strip()


def _views(text: str):
    norm = normalize(text)
    return norm, skeleton(translit(norm))


def family_claim(text: str, family_names: List[str] = ()) -> List[str]:
    norm, roman = _views(text)
    names = [n.strip() for n in family_names if n and n.strip()]
    hits = find_phrases(norm, CONFIG["family_words"] + names, roman)
    return hits


# ---------------------------------------------------------------- code word

def check_code_word(answer: str, code_words: List[str], threshold: float = 0.8) -> bool:
    """Fuzzy match the spoken answer against the family code word(s).

    Compares on a Roman skeleton so 'gulmohar', 'गुलमोहर' and a noisy 'गुलमोहा'
    all match, while unrelated words do not.
    """
    _, roman = _views(answer)
    tokens = roman.split()
    for cw in code_words:
        cw = cw.strip()
        if not cw:
            continue
        target = skeleton(translit(normalize(cw))).replace(" ", "")
        n = max(1, len(cw.split()))
        for i in range(len(tokens)):
            for k in (n, n + 1):
                cand = "".join(tokens[i:i + k])
                if cand and difflib.SequenceMatcher(None, cand, target).ratio() >= threshold:
                    return True
    return False


# ---------------------------------------------------------------- verdict

PRESSURE = {"money", "family_emergency", "urgency", "secrecy", "credentials", "remote_access"}


def assess(text: str, family_names: List[str] = (), code_word_status: str = "not_asked") -> dict:
    """Assess a (cumulative) caller transcript.

    code_word_status: not_asked | correct | wrong | missing   (code word is optional)
    """
    norm, roman = _views(text)
    fam = family_claim(text, family_names)
    matches: Dict[str, List[str]] = {}
    for key, cat in CONFIG["categories"].items():
        t_norm, t_roman = norm, roman
        if cat.get("exclude"):
            t_norm = _remove(norm, cat["exclude"])
            t_roman = _remove(roman, [skeleton(e) for e in cat["exclude"] if _is_roman(e)])
        hits = find_phrases(t_norm, cat["phrases"], t_roman)
        if hits and cat.get("requires_family") and not fam:
            hits = []
        if hits:
            matches[key] = hits

    reasons = [CONFIG["categories"][k]["label"] for k in matches]

    # Family claims from an unknown number are verified by CALL-BACK, not by the
    # assistant. A claim alone is "unverified" (yellow); a claim + pressure
    # (money / emergency / urgency / secrecy / credentials / remote access) is
    # the classic "relative in trouble" script (red). The optional code word
    # only matters if the family turned it on: correct = verified, wrong = red.
    unverified_family = bool(fam) and code_word_status != "correct"
    pressure = [k for k in matches if k in PRESSURE]
    if unverified_family:
        reasons.insert(0, "Unverified family claim")
    if code_word_status == "wrong":
        reasons.append("Code word wrong")

    if ("credentials" in matches or len(matches) >= 2 or code_word_status == "wrong"
            or (unverified_family and pressure)):
        verdict = RED
    elif len(matches) == 1 or unverified_family:
        verdict = YELLOW
    else:
        verdict = GREEN

    return {
        "verdict": verdict,
        "categories": list(matches.keys()),
        "matches": matches,
        "reasons": reasons,
        "family_claim": fam,
        "verify_by_callback": unverified_family,
        "code_word_status": code_word_status,
    }


def benign_intent(text: str) -> dict:
    """Detect simple benign intents + time words for the parent's message summary."""
    norm, roman = _views(text)
    intents = [k for k, ph in CONFIG["benign_intents"].items() if find_phrases(norm, ph, roman)]
    times = [k for k, ph in CONFIG["time_words"].items() if find_phrases(norm, ph)]
    return {"intents": intents, "times": times}
