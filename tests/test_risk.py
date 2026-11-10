import json
from pathlib import Path

import pytest

from app.risk import GREEN, RED, YELLOW, assess, benign_intent, check_code_word, family_claim

FAMILY = ["Rohit", "Priya"]

# (transcript, expected verdict, categories that must be present)
CASES = [
    # --- acceptance lines (typed Hinglish) ---
    ("Main CBI se bol raha hoon, aapke naam pe case hai, OTP batao", RED, {"authority", "credentials"}),
    ("Aunty, Rohit ka accident ho gaya, turant paise bhejo", RED, {"family_emergency", "urgency", "money"}),
    ("Amazon delivery hai, kal aaunga, ghar pe koi hoga?", GREEN, set()),
    ("Bijli vibhag se, aaj raat light kat jayegi", RED, {"authority", "urgency"}),
    # --- every category on its own ---
    ("Apna ATM pin bata dijiye", RED, {"credentials"}),            # credentials alone -> red
    ("Main police station se bol raha hoon", YELLOW, {"authority"}),
    ("Yeh kaam turant hona chahiye", YELLOW, {"urgency"}),
    ("Yeh baat kisi ko mat batana", YELLOW, {"secrecy"}),
    ("Aapko refund milega, bas form bhariye", YELLOW, {"money"}),
    ("Ek AnyDesk app install kar lijiye", YELLOW, {"remote_access"}),
    ("Aapke beta ka accident ho gaya hai", RED, {"family_emergency"}),   # unverified family + emergency
    # --- combinations ---
    ("Customs mein aapka parcel pakda gaya hai, drugs mile hain, fine bharo warna arrest", RED,
     {"authority", "money", "urgency"}),
    ("Main bank se, aapka account band ho jayega, link pe click karo", RED, {"urgency", "remote_access"}),
    ("Galti se aapke account mein paise chale gaye, wapas bhej do please", YELLOW, {"money"}),
    ("Video call pe raho aur phone mat kaatna, CBI officer baat karenge", RED, {"secrecy", "authority"}),
    # --- Devanagari (real Prisma codemix style) ---
    ("मैं CBI से बोल रहा हूँ, आपके नाम पर case है, OTP बताओ।", RED, {"authority", "credentials"}),
    ("आंटी, रोहित का accident हो गया, तुरंत पैसे भेजो।", RED, {"family_emergency", "urgency", "money"}),
    ("Amazon delivery है, कल आऊँगा। घर पे कोई होगा?", GREEN, set()),
    ("बिजली विभाग से बोल रहा हूँ, आज रात light cut जाएगी।", RED, {"authority", "urgency"}),
    ("आपको गिरफ्तारी का वारंट जारी हुआ है", RED, {"urgency", "authority"}),
    ("किसी को मत बताइए, वीडियो कॉल पर रहिए", YELLOW, {"secrecy"}),
    ("आपके नाम पे case है, बोली भी बता।", YELLOW, {"urgency"}),     # real noisy Prisma output, OTP lost
    ("मैं CBI officer वर्मा बोल रहा हूँ। Cyber Cell, Delhi Cell. आपके नाम पे case है, बोली भी बता।", RED,
     {"authority", "urgency"}),                                      # same, cumulative over the call
    # --- Kannada ---
    ("ನಾನು ಪೊಲೀಸ್ ಠಾಣೆಯಿಂದ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ, ತಕ್ಷಣ ಹಣ ಕಳುಹಿಸಿ", RED, {"authority", "urgency", "money"}),
    ("ನಿಮ್ಮ ಒಟಿಪಿ ಹೇಳಿ", RED, {"credentials"}),
    ("ನಾಳೆ ಪಾರ್ಸೆಲ್ ಡೆಲಿವರಿ ಇದೆ", GREEN, set()),
    # --- benign calls (must stay green) ---
    ("Main Ramesh, aapka padosi, kal shaam ko milne aaunga", GREEN, set()),
    ("Doctor clinic se bol rahe hain, aapka appointment kal subah das baje hai", GREEN, set()),
    ("Courier hai, pin code confirm karna tha, 560001 sahi hai?", GREEN, set()),
    ("Gas cylinder ki delivery aaj shaam ko hogi, cash on delivery hai", GREEN, set()),
    ("Main theek hoon, fine, abhi bahar hoon, phir call karunga", GREEN, set()),
    ("नमस्ते, मैं पड़ोस से शर्मा आंटी की बेटी की सहेली बोल रही हूँ", YELLOW, set()),  # mentions family: call back, no pressure
]


@pytest.mark.parametrize("text,verdict,cats", CASES)
def test_verdicts(text, verdict, cats):
    r = assess(text, FAMILY)
    assert r["verdict"] == verdict, (text, r)
    assert cats <= set(r["categories"]), (text, r)
    if verdict == GREEN:
        assert r["categories"] == []


def test_reasons_are_human_readable():
    r = assess("Main CBI se bol raha hoon, aapke naam pe case hai, OTP batao", FAMILY)
    assert "Authority claim" in r["reasons"] and "Credentials request" in r["reasons"]
    assert "cbi" in r["matches"]["authority"] and "otp" in r["matches"]["credentials"]


def test_family_emergency_needs_family_mention():
    assert "family_emergency" not in assess("Road pe accident dekha maine", FAMILY)["categories"]
    assert "family_emergency" in assess("Rohit hospital mein hai", FAMILY)["categories"]


# --- code word branch ---

def test_family_claim_detection():
    assert family_claim("Main aapka beta bol raha hoon", FAMILY)
    assert family_claim("रोहित बोल रहा हूँ", FAMILY)
    assert family_claim("Hello, main Rohit", FAMILY)
    assert not family_claim("Amazon delivery hai", FAMILY)


@pytest.mark.parametrize("answer,ok", [
    ("gulmohar", True), ("Code word hai Gulmohar.", True), ("code word है गुलमोहर।", True),
    ("Good word है गुलमोहा।", True),           # real noisy Prisma output
    ("mujhe yaad nahi", False), ("gulab", False), ("", False), ("jamun", False),
])
def test_code_word(answer, ok):
    assert check_code_word(answer, ["gulmohar"]) is ok


def test_wrong_code_word_forces_red():
    r = assess("Main Rohit bol raha hoon, naya number hai", FAMILY, code_word_status="wrong")
    assert r["verdict"] == RED and "Code word wrong" in r["reasons"]


# --- family claims: verify by call-back (code word is optional) ---

@pytest.mark.parametrize("text,verdict", [
    # claim alone, no pressure -> unverified, family calls back (not a scam alert)
    ("Main Sharma ji ka bhatija bol raha hoon, shaadi ka card dena tha", YELLOW),
    ("Main Rohit bol raha hoon, naya number hai", YELLOW),
    ("रोहित बोल रहा हूँ, घर कब आऊँ बस यह पूछना था", YELLOW),
    # claim + any pressure -> the "relative in trouble" script
    ("Main Rohit bol raha hoon, mujhe paise bhej do", RED),                      # + money
    ("Papa main Rohit, kisi ko mat batana", RED),                                # + secrecy
    ("Aapka beta hospital mein hai", RED),                                        # + emergency
    ("Main aapka pota, turant call karo", RED),                                   # + urgency
])
def test_family_claim_callback_rules(text, verdict):
    r = assess(text, FAMILY)
    assert r["verdict"] == verdict, (text, r)
    assert r["verify_by_callback"] and r["reasons"][0] == "Unverified family claim"


def test_missing_code_word_is_unverified_not_red():
    r = assess("Main Rohit bol raha hoon, naya number hai", FAMILY, code_word_status="missing")
    assert r["verdict"] == YELLOW


def test_correct_code_word_not_red_by_itself():
    r = assess("Main Rohit bol raha hoon, naya number hai", FAMILY, code_word_status="correct")
    assert r["verdict"] == GREEN
    r = assess("Main Rohit bol raha hoon, ghar kab aaun, bas yeh poochna tha, turant", FAMILY,
               code_word_status="correct")
    assert r["verdict"] == YELLOW  # urgency alone, code word did not add red


# --- message summary intents ---

def test_benign_intent():
    b = benign_intent("Amazon delivery hai, kal aaunga, ghar pe koi hoga?")
    assert "delivery" in b["intents"] and "tomorrow" in b["times"]
    assert "clinic" in benign_intent("डॉक्टर क्लिनिक से, अपॉइंटमेंट कल है")["intents"]


# --- real Prisma v3.0 transcripts (Timbre-synthesized caller, 8 kHz, clean + noisy) ---

FIXTURES = Path(__file__).parent / "fixtures" / "prisma_transcripts.json"
EXPECT = {"cbi": RED, "relative": RED, "delivery": GREEN, "bijli": RED}


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/roundtrip.py to create fixtures")
def test_real_prisma_transcripts():
    data = json.loads(FIXTURES.read_text())
    checked = 0
    for key, row in data.items():
        line = key.split("|")[0]
        if line in EXPECT:
            assert assess(row["transcript"], FAMILY)["verdict"] == EXPECT[line], (key, row)
            checked += 1
        elif line == "codeword":
            assert check_code_word(row["transcript"], ["gulmohar"]), (key, row)
    assert checked >= 8


# --- multilingual (Gena mirrors the caller; family hears their own language) ---

from app import lang as L  # noqa: E402


@pytest.mark.parametrize("text,verdict", [
    ("I am calling from the CBI. There is a case against you. Tell me the O T P now.", RED),     # real Prisma output
    ("Your account will be blocked tonight, send money and don't tell anyone", RED),
    ("Hi, this is the courier, I'll deliver your parcel tomorrow, will someone be home?", GREEN),
    ("நான் police station-ல இருந்து பேசுகிறேன், உடனே பணம் அனுப்புங்கள்.", RED),                 # real Prisma output
    ("নমস্কার, কাল আপনার পার্সেল ডেলিভারি হবে।", GREEN),
    ("আমি ব্যাংক থেকে বলছি। আপনার OTP বলুন, কাউকে বলবেন না।", RED),                              # real Prisma output
    ("నేను పోలీస్ స్టేషన్ నుండి మాట్లాడుతున్నాను, వెంటనే డబ్బు పంపండి", RED),
    ("मी पोलीस स्टेशनमधून बोलतो आहे, लगेच पैसे पाठवा", RED),
    ("Main aapka padosi hoon, kal milne aaunga", GREEN),
])
def test_multilingual_verdicts(text, verdict):
    assert assess(text, FAMILY)["verdict"] == verdict, (text, assess(text, FAMILY))


@pytest.mark.parametrize("text,prisma,expected", [
    ("I am calling from the CBI.", "en-IN", "en-IN"),
    ("Main CBI se bol raha hoon, OTP batao", None, "hi-IN"),        # Roman Hinglish, typed
    ("मैं CBI से बोल रहा हूँ", "hi-IN", "hi-IN"),
    ("मी पोलीस स्टेशनमधून बोलतो आहे", "hi-IN", "mr-IN"),              # Marathi in Devanagari
    ("நான் police station-ல இருந்து பேசுகிறேன்", "ta-IN", "ta-IN"),
    ("আমি bank থেকে বলছি", None, "bn-IN"),
    ("ನಾಳೆ ಪಾರ್ಸೆಲ್ ಡೆಲಿವರಿ ಇದೆ", None, "kn-IN"),
])
def test_detect_language(text, prisma, expected):
    assert L.detect(text, prisma) == expected


def test_every_language_has_every_line():
    for code in L.LANGS:
        lines = L.lines("Sharma ji", code)
        assert set(lines) == {"name", "org", "purpose", "codeword", "relation", "reask",
                              "close_green", "close_yellow", "close_family", "close_red"}
        assert all(t for t, _, _ in lines.values())
        assert set(L.RELAY[code]) >= {"intro", "delivery", "outro", "fallback", "fallback_other"}


def test_relay_uses_family_language_not_callers():
    intent = {"intents": [], "times": []}
    # English caller, Hindi-only family, no template fits -> Hindi notice, never English audio
    clips = L.parent_message(intent, "I wanted to discuss an insurance plan", "hi-IN", "en-IN")
    assert clips == [(L.RELAY["hi-IN"]["intro"] + " " + L.RELAY["hi-IN"]["fallback_other"], "hi-IN")]
    # same language -> their own words are played after the intro
    clips = L.parent_message(intent, "Bas haal chaal poochna tha", "hi-IN", "hi-IN")
    assert clips[1] == ("Bas haal chaal poochna tha", "hi-IN")
    # known intent -> template in the family's language
    clips = L.parent_message({"intents": ["delivery"], "times": ["tomorrow"]}, "", "ta-IN", "en-IN")
    assert clips[0][1] == "ta-IN" and L.RELAY["ta-IN"]["tomorrow"] in clips[0][0]
