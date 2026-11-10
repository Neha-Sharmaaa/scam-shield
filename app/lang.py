"""Language pack for Gena (the Scam Shield assistant) and for messages relayed to the parent.

Gena greets in the family's language, then replies in the language the caller actually speaks
(detected by Gnani Prisma `indic-auto`). Messages relayed to the parent always use the family's
language. Each line is (tts_text, display_text, display_sub). Translations are hand-written:
have a native speaker review each language before real use.
"""
import re

# code -> (English name, native name)
LANGS = {
    "hi-IN": ("Hindi", "हिन्दी"),
    "en-IN": ("English", "English"),
    "kn-IN": ("Kannada", "ಕನ್ನಡ"),
    "ta-IN": ("Tamil", "தமிழ்"),
    "te-IN": ("Telugu", "తెలుగు"),
    "mr-IN": ("Marathi", "मराठी"),
    "bn-IN": ("Bengali", "বাংলা"),
}
DEFAULT = "hi-IN"
SPOKEN_EN = "Jeena"   # how Timbre should pronounce the name in English (verified via Prisma round-trip)

# ---------------------------------------------------------------- Gena's lines to the caller
# {p} = parent's name. Hindi shows Roman Hinglish with Devanagari below; other Indic languages
# show the native script with an English gloss below.
_EN = {
    "name": "Hello, this is Gena, {p}'s assistant. May I know who is calling?",
    "org": "Which company or department are you calling from?",
    "purpose": "What is the reason for your call?",
    "codeword": "Please tell me the family code word.",
    "relation": "How are you related to the family? Please tell me your full name.",
    "reask": "Sorry, I couldn't hear that clearly.",
    "close_green": "Thank you. I will pass on your message.",
    "close_yellow": "Thank you. The family will get back to you.",
    "close_family": "Thank you. I'll let the family know. They will call you back on the number they already have.",
    "close_red": "Thank you. This call is now being ended.",
}

_LINES = {
    "hi-IN": {
        "name": ("नमस्ते, मैं जीना बोल रही हूँ, {p} की सहायक। आप कौन बोल रहे हैं?", "Namaste, main Gena bol rahi hoon, {p} ki sahayak. Aap kaun bol rahe hain?"),
        "org": ("आप किस कंपनी या विभाग से बोल रहे हैं?", "Aap kis company ya vibhag se bol rahe hain?"),
        "purpose": ("आपने किस काम के लिए कॉल किया है?", "Aapne kis kaam ke liye call kiya hai?"),
        "codeword": ("कृपया परिवार का कोड वर्ड बताइए।", "Kripya parivaar ka code word batayein."),
        "relation": ("आपका परिवार से क्या रिश्ता है? अपना पूरा नाम बताइए।", "Aapka parivaar se kya rishta hai? Apna poora naam batayein."),
        "reask": ("माफ़ कीजिए, आवाज़ साफ़ नहीं आई।", "Maaf kijiye, awaaz saaf nahi aayi."),
        "close_green": ("धन्यवाद, मैं आपका संदेश पहुँचा दूँगी।", "Dhanyavaad, main aapka sandesh pahuncha dungi."),
        "close_yellow": ("धन्यवाद, परिवार आपसे संपर्क करेगा।", "Dhanyavaad, parivaar aapse sampark karega."),
        "close_family": ("धन्यवाद। मैं घर वालों को बता दूँगी, वो आपको उसी नंबर पर कॉल करेंगे जो उनके पास पहले से है।",
                         "Dhanyavaad. Main ghar walon ko bata dungi, woh aapko usi number par call karenge jo unke paas pehle se hai."),
        "close_red": ("धन्यवाद। यह कॉल समाप्त की जा रही है।", "Dhanyavaad. Yeh call samaapt ki ja rahi hai."),
    },
    "kn-IN": {
        "name": "ನಮಸ್ಕಾರ, ನಾನು ಜೀನಾ, {p} ಅವರ ಸಹಾಯಕಿ. ಯಾರು ಮಾತನಾಡುತ್ತಿದ್ದೀರಿ?",
        "org": "ನೀವು ಯಾವ ಕಂಪನಿ ಅಥವಾ ಇಲಾಖೆಯಿಂದ ಕರೆ ಮಾಡುತ್ತಿದ್ದೀರಿ?",
        "purpose": "ನೀವು ಯಾವ ಕೆಲಸಕ್ಕಾಗಿ ಕರೆ ಮಾಡಿದ್ದೀರಿ?",
        "codeword": "ದಯವಿಟ್ಟು ಕುಟುಂಬದ ಕೋಡ್ ವರ್ಡ್ ಹೇಳಿ.",
        "relation": "ಕುಟುಂಬದೊಂದಿಗೆ ನಿಮ್ಮ ಸಂಬಂಧವೇನು? ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರು ಹೇಳಿ.",
        "reask": "ಕ್ಷಮಿಸಿ, ಸರಿಯಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ.",
        "close_green": "ಧನ್ಯವಾದಗಳು, ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ತಲುಪಿಸುತ್ತೇನೆ.",
        "close_yellow": "ಧನ್ಯವಾದಗಳು, ಕುಟುಂಬದವರು ನಿಮ್ಮನ್ನು ಸಂಪರ್ಕಿಸುತ್ತಾರೆ.",
        "close_family": "ಧನ್ಯವಾದಗಳು. ನಾನು ಮನೆಯವರಿಗೆ ತಿಳಿಸುತ್ತೇನೆ, ಅವರ ಬಳಿ ಈಗಾಗಲೇ ಇರುವ ನಂಬರ್‌ಗೆ ಅವರು ನಿಮಗೆ ಕರೆ ಮಾಡುತ್ತಾರೆ.",
        "close_red": "ಧನ್ಯವಾದಗಳು. ಈ ಕರೆಯನ್ನು ಈಗ ಕೊನೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ.",
    },
    "ta-IN": {
        "name": "வணக்கம், நான் ஜீனா, {p} அவர்களின் உதவியாளர். யார் பேசுகிறீர்கள்?",
        "org": "நீங்கள் எந்த நிறுவனம் அல்லது துறையிலிருந்து பேசுகிறீர்கள்?",
        "purpose": "நீங்கள் எதற்காக அழைத்தீர்கள்?",
        "codeword": "தயவுசெய்து குடும்பத்தின் கோட் வேர்டைச் சொல்லுங்கள்.",
        "relation": "குடும்பத்துடன் உங்கள் உறவு என்ன? உங்கள் முழுப் பெயரைச் சொல்லுங்கள்.",
        "reask": "மன்னிக்கவும், சரியாகக் கேட்கவில்லை.",
        "close_green": "நன்றி, உங்கள் செய்தியை நான் தெரிவிக்கிறேன்.",
        "close_yellow": "நன்றி, குடும்பத்தினர் உங்களைத் தொடர்பு கொள்வார்கள்.",
        "close_family": "நன்றி. நான் வீட்டினரிடம் சொல்கிறேன், அவர்களிடம் ஏற்கனவே உள்ள எண்ணில் அவர்கள் உங்களை அழைப்பார்கள்.",
        "close_red": "நன்றி. இந்த அழைப்பு இப்போது முடிக்கப்படுகிறது.",
    },
    "te-IN": {
        "name": "నమస్కారం, నేను జీనా, {p} గారి సహాయకురాలిని. ఎవరు మాట్లాడుతున్నారు?",
        "org": "మీరు ఏ కంపెనీ లేదా విభాగం నుండి మాట్లాడుతున్నారు?",
        "purpose": "మీరు ఏ పని కోసం కాల్ చేశారు?",
        "codeword": "దయచేసి కుటుంబ కోడ్ వర్డ్ చెప్పండి.",
        "relation": "కుటుంబంతో మీ సంబంధం ఏమిటి? దయచేసి మీ పూర్తి పేరు చెప్పండి.",
        "reask": "క్షమించండి, సరిగ్గా వినిపించలేదు.",
        "close_green": "ధన్యవాదాలు, మీ సందేశాన్ని నేను తెలియజేస్తాను.",
        "close_yellow": "ధన్యవాదాలు, కుటుంబ సభ్యులు మిమ్మల్ని సంప్రదిస్తారు.",
        "close_family": "ధన్యవాదాలు. నేను ఇంట్లో వాళ్ళకి చెబుతాను, వారి దగ్గర ఇప్పటికే ఉన్న నంబర్‌కు వారు మీకు కాల్ చేస్తారు.",
        "close_red": "ధన్యవాదాలు. ఈ కాల్ ఇప్పుడు ముగించబడుతోంది.",
    },
    "mr-IN": {
        "name": "नमस्कार, मी जीना बोलते आहे, {p} यांची सहाय्यक. आपण कोण बोलत आहात?",
        "org": "आपण कोणत्या कंपनी किंवा विभागातून बोलत आहात?",
        "purpose": "आपण कोणत्या कामासाठी फोन केला आहे?",
        "codeword": "कृपया कुटुंबाचा कोड वर्ड सांगा.",
        "relation": "कुटुंबाशी आपले नाते काय आहे? कृपया आपले पूर्ण नाव सांगा.",
        "reask": "माफ करा, नीट ऐकू आले नाही.",
        "close_green": "धन्यवाद, मी आपला संदेश पोहोचवेन.",
        "close_yellow": "धन्यवाद, कुटुंबीय आपल्याशी संपर्क साधतील.",
        "close_family": "धन्यवाद. मी घरच्यांना सांगेन, त्यांच्याकडे आधीपासून असलेल्या नंबरवर ते आपल्याला फोन करतील.",
        "close_red": "धन्यवाद. हा कॉल आता संपवला जात आहे.",
    },
    "bn-IN": {
        "name": "নমস্কার, আমি জীনা, {p}-এর সহকারী। কে বলছেন?",
        "org": "আপনি কোন কোম্পানি বা বিভাগ থেকে বলছেন?",
        "purpose": "আপনি কী কাজে ফোন করেছেন?",
        "codeword": "অনুগ্রহ করে পরিবারের কোড ওয়ার্ডটি বলুন।",
        "relation": "পরিবারের সঙ্গে আপনার সম্পর্ক কী? অনুগ্রহ করে আপনার পুরো নাম বলুন।",
        "reask": "দুঃখিত, ঠিকমতো শুনতে পেলাম না।",
        "close_green": "ধন্যবাদ, আমি আপনার বার্তা পৌঁছে দেব।",
        "close_yellow": "ধন্যবাদ, পরিবারের লোকেরা আপনার সঙ্গে যোগাযোগ করবেন।",
        "close_family": "ধন্যবাদ। আমি বাড়ির লোকদের জানাব, তাঁদের কাছে আগে থেকে থাকা নম্বরে তাঁরা আপনাকে ফোন করবেন।",
        "close_red": "ধন্যবাদ। এই কলটি এখন শেষ করা হচ্ছে।",
    },
}


def lines(parent_name: str, lang: str) -> dict:
    """{key: (tts_text, display_text, display_sub)} for Gena, in `lang`."""
    lang = lang if lang in LANGS else DEFAULT
    out = {}
    for key, en in _EN.items():
        en = en.format(p=parent_name)
        if lang == "en-IN":
            out[key] = (en.replace("Gena", SPOKEN_EN), en, "")   # TTS says "Jeena"; screen shows "Gena"
        elif lang == "hi-IN":
            dev, roman = _LINES["hi-IN"][key]
            dev, roman = dev.format(p=parent_name), roman.format(p=parent_name)
            out[key] = (dev, roman, dev)
        else:
            native = _LINES[lang][key].format(p=parent_name)
            out[key] = (native, native, en)
    return out


# ---------------------------------------------------------------- messages relayed to the parent
RELAY = {
    "hi-IN": {"intro": "पापा, आपके लिए एक कॉल आया था।", "delivery": "आपका पार्सल डिलीवरी आने वाला है।",
              "clinic": "डॉक्टर के क्लिनिक से कॉल था, आपके अपॉइंटमेंट के बारे में।", "neighbour": "पड़ोसी का कॉल आया था।",
              "gas": "गैस सिलेंडर के बारे में कॉल आया था।", "repair": "मरम्मत वाले का कॉल आया था।",
              "tomorrow": "वो कल आएँगे।", "today": "वो आज आएँगे।", "day_after": "वो परसों आएँगे।", "delivery_home": "घर पर कोई रहे।",
              "fallback": "उनका संदेश है:", "fallback_other": "उनका संदेश दूसरी भाषा में था, घर वाले आपको बता देंगे।",
              "outro": "इस कॉल की जाँच परिवार ने कर ली है।"},
    "en-IN": {"intro": "Papa, you had a call.", "delivery": "Your parcel delivery is on its way.",
              "clinic": "The doctor's clinic called about your appointment.", "neighbour": "A neighbour called.",
              "gas": "There was a call about your gas cylinder.", "repair": "The repair person called.",
              "tomorrow": "They will come tomorrow.", "today": "They will come today.", "day_after": "They will come the day after tomorrow.",
              "delivery_home": "Please make sure someone is at home.", "fallback": "Here is their message:",
              "fallback_other": "Their message was in another language. The family will explain it to you.",
              "outro": "The family has checked this call."},
    "kn-IN": {"intro": "ಅಪ್ಪಾ, ನಿಮಗೆ ಒಂದು ಕರೆ ಬಂದಿತ್ತು.", "delivery": "ನಿಮ್ಮ ಪಾರ್ಸೆಲ್ ಡೆಲಿವರಿ ಬರುತ್ತಿದೆ.",
              "clinic": "ಡಾಕ್ಟರ್ ಕ್ಲಿನಿಕ್‌ನಿಂದ ಕರೆ ಬಂದಿತ್ತು, ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಬಗ್ಗೆ.", "neighbour": "ನೆರೆಹೊರೆಯವರು ಕರೆ ಮಾಡಿದ್ದರು.",
              "gas": "ಗ್ಯಾಸ್ ಸಿಲಿಂಡರ್ ಬಗ್ಗೆ ಕರೆ ಬಂದಿತ್ತು.", "repair": "ರಿಪೇರಿ ಕೆಲಸದವರು ಕರೆ ಮಾಡಿದ್ದರು.",
              "tomorrow": "ಅವರು ನಾಳೆ ಬರುತ್ತಾರೆ.", "today": "ಅವರು ಇಂದು ಬರುತ್ತಾರೆ.", "day_after": "ಅವರು ನಾಡಿದ್ದು ಬರುತ್ತಾರೆ.",
              "delivery_home": "ಮನೆಯಲ್ಲಿ ಯಾರಾದರೂ ಇರಲಿ.", "fallback": "ಅವರ ಸಂದೇಶ ಹೀಗಿದೆ:",
              "fallback_other": "ಅವರ ಸಂದೇಶ ಬೇರೆ ಭಾಷೆಯಲ್ಲಿತ್ತು, ಮನೆಯವರು ನಿಮಗೆ ತಿಳಿಸುತ್ತಾರೆ.", "outro": "ಈ ಕರೆಯನ್ನು ಕುಟುಂಬದವರು ಪರಿಶೀಲಿಸಿದ್ದಾರೆ."},
    "ta-IN": {"intro": "அப்பா, உங்களுக்கு ஒரு அழைப்பு வந்தது.", "delivery": "உங்கள் பார்சல் டெலிவரி வருகிறது.",
              "clinic": "மருத்துவரின் கிளினிக்கிலிருந்து உங்கள் அப்பாயிண்ட்மெண்ட் பற்றி அழைத்தார்கள்.", "neighbour": "பக்கத்து வீட்டுக்காரர் அழைத்தார்.",
              "gas": "கேஸ் சிலிண்டர் பற்றி அழைப்பு வந்தது.", "repair": "ரிப்பேர் செய்பவர் அழைத்தார்.",
              "tomorrow": "அவர்கள் நாளை வருவார்கள்.", "today": "அவர்கள் இன்று வருவார்கள்.", "day_after": "அவர்கள் நாளை மறுநாள் வருவார்கள்.",
              "delivery_home": "வீட்டில் யாராவது இருங்கள்.", "fallback": "அவர்களின் செய்தி:",
              "fallback_other": "அவர்களின் செய்தி வேறு மொழியில் இருந்தது, வீட்டினர் உங்களுக்குச் சொல்வார்கள்.",
              "outro": "இந்த அழைப்பை குடும்பத்தினர் சரிபார்த்துள்ளனர்."},
    "te-IN": {"intro": "నాన్నా, మీకు ఒక కాల్ వచ్చింది.", "delivery": "మీ పార్సెల్ డెలివరీ వస్తోంది.",
              "clinic": "డాక్టర్ క్లినిక్ నుండి మీ అపాయింట్‌మెంట్ గురించి కాల్ వచ్చింది.", "neighbour": "పక్కింటి వారు కాల్ చేశారు.",
              "gas": "గ్యాస్ సిలిండర్ గురించి కాల్ వచ్చింది.", "repair": "రిపేర్ చేసే వ్యక్తి కాల్ చేశారు.",
              "tomorrow": "వారు రేపు వస్తారు.", "today": "వారు ఈరోజు వస్తారు.", "day_after": "వారు ఎల్లుండి వస్తారు.",
              "delivery_home": "ఇంట్లో ఎవరైనా ఉండండి.", "fallback": "వారి సందేశం:",
              "fallback_other": "వారి సందేశం వేరే భాషలో ఉంది, ఇంట్లో వాళ్ళు మీకు చెబుతారు.", "outro": "ఈ కాల్‌ను కుటుంబ సభ్యులు తనిఖీ చేశారు."},
    "mr-IN": {"intro": "बाबा, तुम्हाला एक फोन आला होता.", "delivery": "तुमचे पार्सल डिलिव्हरीसाठी येत आहे.",
              "clinic": "डॉक्टरांच्या क्लिनिकमधून तुमच्या अपॉइंटमेंटबद्दल फोन आला होता.", "neighbour": "शेजाऱ्यांचा फोन आला होता.",
              "gas": "गॅस सिलेंडरबद्दल फोन आला होता.", "repair": "दुरुस्ती करणाऱ्याचा फोन आला होता.",
              "tomorrow": "ते उद्या येतील.", "today": "ते आज येतील.", "day_after": "ते परवा येतील.", "delivery_home": "घरी कोणीतरी असू द्या.",
              "fallback": "त्यांचा संदेश असा आहे:", "fallback_other": "त्यांचा संदेश दुसऱ्या भाषेत होता, घरचे तुम्हाला सांगतील.",
              "outro": "या कॉलची कुटुंबाने तपासणी केली आहे."},
    "bn-IN": {"intro": "বাবা, আপনার একটা ফোন এসেছিল।", "delivery": "আপনার পার্সেল ডেলিভারি আসছে।",
              "clinic": "ডাক্তারের ক্লিনিক থেকে আপনার অ্যাপয়েন্টমেন্টের ব্যাপারে ফোন এসেছিল।", "neighbour": "প্রতিবেশী ফোন করেছিলেন।",
              "gas": "গ্যাস সিলিন্ডারের ব্যাপারে ফোন এসেছিল।", "repair": "মেরামতের লোক ফোন করেছিলেন।",
              "tomorrow": "ওঁরা কাল আসবেন।", "today": "ওঁরা আজ আসবেন।", "day_after": "ওঁরা পরশু আসবেন।", "delivery_home": "বাড়িতে কেউ থাকবেন।",
              "fallback": "ওঁদের বার্তা:", "fallback_other": "ওঁদের বার্তা অন্য ভাষায় ছিল, বাড়ির লোকেরা আপনাকে বুঝিয়ে দেবেন।",
              "outro": "পরিবার এই কলটি যাচাই করেছে।"},
}


def parent_message(intent: dict, purpose_text: str, family_lang: str, caller_lang: str) -> list:
    """Clips [(text, tts_language)] for the parent, always in the FAMILY's language.

    Known benign intents use templates. Otherwise, if the caller spoke the family's language,
    their own words are played after a short intro; if not, the parent is told (in their
    language) that the family will explain, instead of hearing a language they don't speak.
    """
    fl = family_lang if family_lang in RELAY else DEFAULT
    T = RELAY[fl]
    parts = [T["intro"]]
    if intent["intents"]:
        for i in intent["intents"][:2]:
            parts.append(T[i])
        for t in ("today", "tomorrow", "day_after"):
            if t in intent["times"]:
                parts.append(T[t]); break
        if "delivery" in intent["intents"]:
            parts.append(T["delivery_home"])
        parts.append(T["outro"])
        return [(" ".join(parts), fl)]
    if caller_lang == fl and purpose_text.strip():
        return [(" ".join(parts + [T["fallback"]]), fl), (purpose_text.strip(), fl)]
    return [(" ".join(parts + [T["fallback_other"]]), fl)]


# ---------------------------------------------------------------- language detection
_BLOCKS = [("kn-IN", 0x0C80, 0x0CFF), ("ta-IN", 0x0B80, 0x0BFF), ("te-IN", 0x0C00, 0x0C7F),
           ("bn-IN", 0x0980, 0x09FF), ("hi-IN", 0x0900, 0x097F)]
_HINGLISH = {"hai", "hain", "hoon", "hu", "kya", "aap", "aapka", "aapke", "main", "mein", "nahi", "nahin", "raha", "rahi",
             "karo", "kar", "bhejo", "batao", "ka", "ki", "ke", "ko", "se", "tha", "thi", "ho", "gaya", "bol", "beta", "ji", "kal"}
_MARATHI = {"आहे", "आहात", "आहोत", "मी", "तुम्ही", "आपण", "नाही", "बोलतो", "बोलते", "करा", "पाठवा", "सांगा", "लगेच"}


def detect(text: str, prisma_code: str = None) -> str:
    """Best guess of the caller's language. Prisma's detected_language_code wins when present;
    Latin text is split into English vs Roman Hinglish, Devanagari into Hindi vs Marathi."""
    # split on whitespace/punctuation only: \w does not match Indic vowel signs
    words = [w for w in re.split(r"[\s.,!?;:'\"()\[\]\u0964\u0965-]+", (text or "").lower()) if w]
    if prisma_code in LANGS and prisma_code not in ("en-IN", "hi-IN"):
        return prisma_code
    counts = {}
    for ch in text or "":
        o = ord(ch)
        for code, a, b in _BLOCKS:
            if a <= o <= b:
                counts[code] = counts.get(code, 0) + 1
    if counts:
        best = max(counts, key=counts.get)
        if best == "hi-IN" and sum(w in _MARATHI for w in words) >= 2:
            return "mr-IN"
        if best == "hi-IN" and prisma_code == "mr-IN":
            return "mr-IN"
        return best
    latin = [w for w in words if re.fullmatch(r"[a-z]+", w)]
    if not latin:
        return prisma_code if prisma_code in LANGS else None
    return "hi-IN" if sum(w in _HINGLISH for w in latin) >= 2 else "en-IN"


# ---------------------------------------------------------------- Gena's call summary for the family
# Spoken to the son/daughter in the family's language: what happened on the call and what Gena did.
LANG_LATIN = {"hi-IN": "Hindi", "en-IN": "English", "kn-IN": "Kannada", "ta-IN": "Tamil",
              "te-IN": "Telugu", "mr-IN": "Marathi", "bn-IN": "Bengali"}

SUMMARY = {
    "hi-IN": {"intro_red": "एक अनजान नंबर से एक संदिग्ध कॉल आया था।", "intro_yellow": "एक अनजान नंबर से कॉल आया था, जिसकी जाँच ज़रूरी है।",
              "intro_green": "एक अनजान नंबर से कॉल आया था, जो सुरक्षित लगा।",
              "spoke": "कॉलर {lang} में बात कर रहे थे, इसलिए मैंने भी {lang} में जवाब दिया।",
              "credentials": "उन्होंने ओटीपी या बैंक की जानकारी माँगी।", "authority": "उन्होंने खुद को पुलिस या सरकारी अधिकारी बताया।",
              "urgency": "उन्होंने डराया और जल्दी मचाई।", "secrecy": "उन्होंने किसी को न बताने को कहा।", "money": "उन्होंने पैसे माँगे।",
              "remote_access": "उन्होंने एक ऐप डाउनलोड करने को कहा।", "family_emergency": "उन्होंने परिवार में किसी इमरजेंसी की बात कही।",
              "unverified": "उन्होंने खुद को परिवार का बताया।",
              "action_red": "मैंने कॉल विनम्रता से काट दी। पापा से बात नहीं कराई और कोई जानकारी नहीं दी।",
              "action_yellow": "मैंने संदेश ले लिया है। कृपया एक बार देख लीजिए।",
              "action_family": "कृपया उन्हें उसी नंबर पर कॉल करके जाँच लीजिए जो आपके पास पहले से है।",
              "action_green": "मैंने उनका संदेश ले लिया है और पापा को सुना सकती हूँ।"},
    "en-IN": {"intro_red": "An unknown number made a suspicious call.", "intro_yellow": "An unknown number called, and it needs a quick check.",
              "intro_green": "An unknown number called, and it seemed safe.",
              "spoke": "The caller spoke {lang}, so I replied in {lang}.",
              "credentials": "They asked for an OTP or bank details.", "authority": "They claimed to be the police or a government officer.",
              "urgency": "They made threats and created urgency.", "secrecy": "They asked to keep it a secret.", "money": "They asked for money.",
              "remote_access": "They asked to download an app.", "family_emergency": "They talked about a family emergency.",
              "unverified": "They claimed to be family.",
              "action_red": "I ended the call politely. Papa was never connected, and nothing was shared.",
              "action_yellow": "I took a message. Please take a look.",
              "action_family": "Please call them back on a number you already have, to check.",
              "action_green": "I took their message, and I can read it to Papa."},
    "kn-IN": {"intro_red": "ಅಪರಿಚಿತ ನಂಬರ್‌ನಿಂದ ಒಂದು ಅನುಮಾನಾಸ್ಪದ ಕರೆ ಬಂದಿತ್ತು.", "intro_yellow": "ಅಪರಿಚಿತ ನಂಬರ್‌ನಿಂದ ಕರೆ ಬಂದಿತ್ತು, ಅದನ್ನು ಒಮ್ಮೆ ಪರಿಶೀಲಿಸಬೇಕು.",
              "intro_green": "ಅಪರಿಚಿತ ನಂಬರ್‌ನಿಂದ ಕರೆ ಬಂದಿತ್ತು, ಅದು ಸುರಕ್ಷಿತವಾಗಿತ್ತು.",
              "spoke": "ಕರೆ ಮಾಡಿದವರು {lang} ನಲ್ಲಿ ಮಾತನಾಡಿದರು, ಹಾಗಾಗಿ ನಾನೂ {lang} ನಲ್ಲಿ ಉತ್ತರಿಸಿದೆ.",
              "credentials": "ಅವರು ಒಟಿಪಿ ಅಥವಾ ಬ್ಯಾಂಕ್ ವಿವರಗಳನ್ನು ಕೇಳಿದರು.", "authority": "ಅವರು ತಾವು ಪೊಲೀಸ್ ಅಥವಾ ಸರ್ಕಾರಿ ಅಧಿಕಾರಿ ಎಂದು ಹೇಳಿಕೊಂಡರು.",
              "urgency": "ಅವರು ಬೆದರಿಸಿ ಅವಸರ ಮಾಡಿದರು.", "secrecy": "ಯಾರಿಗೂ ಹೇಳಬೇಡಿ ಎಂದು ಹೇಳಿದರು.", "money": "ಅವರು ಹಣ ಕೇಳಿದರು.",
              "remote_access": "ಒಂದು ಆ್ಯಪ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು ಹೇಳಿದರು.", "family_emergency": "ಕುಟುಂಬದಲ್ಲಿ ತುರ್ತು ಪರಿಸ್ಥಿತಿ ಇದೆ ಎಂದು ಹೇಳಿದರು.",
              "unverified": "ಅವರು ತಾವು ಕುಟುಂಬದವರು ಎಂದು ಹೇಳಿಕೊಂಡರು.",
              "action_red": "ನಾನು ಕರೆಯನ್ನು ವಿನಯದಿಂದ ಕೊನೆಗೊಳಿಸಿದೆ. ಅಪ್ಪನಿಗೆ ಕರೆ ಸಂಪರ್ಕಿಸಲಿಲ್ಲ, ಯಾವ ಮಾಹಿತಿಯನ್ನೂ ನೀಡಲಿಲ್ಲ.",
              "action_yellow": "ನಾನು ಸಂದೇಶವನ್ನು ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಒಮ್ಮೆ ನೋಡಿ.",
              "action_family": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಬಳಿ ಈಗಾಗಲೇ ಇರುವ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡಿ ಪರಿಶೀಲಿಸಿ.",
              "action_green": "ನಾನು ಅವರ ಸಂದೇಶವನ್ನು ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ, ಅಪ್ಪನಿಗೆ ಓದಿ ಹೇಳಬಹುದು."},
    "ta-IN": {"intro_red": "தெரியாத எண்ணிலிருந்து ஒரு சந்தேகத்திற்குரிய அழைப்பு வந்தது.", "intro_yellow": "தெரியாத எண்ணிலிருந்து அழைப்பு வந்தது, அதை ஒருமுறை சரிபார்க்க வேண்டும்.",
              "intro_green": "தெரியாத எண்ணிலிருந்து அழைப்பு வந்தது, அது பாதுகாப்பானதாகத் தோன்றியது.",
              "spoke": "அழைத்தவர் {lang}-இல் பேசினார், அதனால் நானும் {lang}-இல் பதில் சொன்னேன்.",
              "credentials": "அவர்கள் ஓடிபி அல்லது வங்கி விவரங்களைக் கேட்டார்கள்.", "authority": "அவர்கள் தங்களை காவல்துறை அல்லது அரசு அதிகாரி என்று சொன்னார்கள்.",
              "urgency": "அவர்கள் மிரட்டி அவசரப்படுத்தினார்கள்.", "secrecy": "யாரிடமும் சொல்ல வேண்டாம் என்று சொன்னார்கள்.", "money": "அவர்கள் பணம் கேட்டார்கள்.",
              "remote_access": "ஒரு ஆப்பை டவுன்லோட் செய்யச் சொன்னார்கள்.", "family_emergency": "குடும்பத்தில் அவசரநிலை என்று சொன்னார்கள்.",
              "unverified": "அவர்கள் தங்களை குடும்பத்தினர் என்று சொன்னார்கள்.",
              "action_red": "நான் அழைப்பை மரியாதையாக முடித்தேன். அப்பாவுடன் இணைக்கவில்லை, எந்தத் தகவலும் கொடுக்கவில்லை.",
              "action_yellow": "நான் செய்தியை எடுத்துக்கொண்டேன். தயவுசெய்து ஒருமுறை பாருங்கள்.",
              "action_family": "உங்களிடம் ஏற்கனவே உள்ள எண்ணில் அவர்களை அழைத்து சரிபார்க்கவும்.",
              "action_green": "நான் அவர்களின் செய்தியை எடுத்துக்கொண்டேன், அப்பாவுக்குப் படித்துச் சொல்ல முடியும்."},
    "te-IN": {"intro_red": "తెలియని నంబర్ నుండి ఒక అనుమానాస్పద కాల్ వచ్చింది.", "intro_yellow": "తెలియని నంబర్ నుండి కాల్ వచ్చింది, దాన్ని ఒకసారి తనిఖీ చేయాలి.",
              "intro_green": "తెలియని నంబర్ నుండి కాల్ వచ్చింది, అది సురక్షితంగా అనిపించింది.",
              "spoke": "కాల్ చేసిన వారు {lang}లో మాట్లాడారు, అందుకే నేను కూడా {lang}లో సమాధానం ఇచ్చాను.",
              "credentials": "వారు ఓటీపీ లేదా బ్యాంక్ వివరాలు అడిగారు.", "authority": "వారు తాము పోలీసు లేదా ప్రభుత్వ అధికారి అని చెప్పుకున్నారు.",
              "urgency": "వారు బెదిరించి తొందరపెట్టారు.", "secrecy": "ఎవరికీ చెప్పవద్దని అన్నారు.", "money": "వారు డబ్బు అడిగారు.",
              "remote_access": "ఒక యాప్ డౌన్‌లోడ్ చేయమని అన్నారు.", "family_emergency": "కుటుంబంలో అత్యవసర పరిస్థితి ఉందని చెప్పారు.",
              "unverified": "వారు తాము కుటుంబ సభ్యులమని చెప్పుకున్నారు.",
              "action_red": "నేను కాల్‌ను మర్యాదగా ముగించాను. నాన్నగారికి కనెక్ట్ చేయలేదు, ఏ సమాచారమూ ఇవ్వలేదు.",
              "action_yellow": "నేను సందేశం తీసుకున్నాను. దయచేసి ఒకసారి చూడండి.",
              "action_family": "దయచేసి మీ దగ్గర ఇప్పటికే ఉన్న నంబర్‌కు కాల్ చేసి తనిఖీ చేయండి.",
              "action_green": "నేను వారి సందేశం తీసుకున్నాను, నాన్నగారికి చదివి వినిపించగలను."},
    "mr-IN": {"intro_red": "एका अनोळखी नंबरवरून एक संशयास्पद कॉल आला होता.", "intro_yellow": "एका अनोळखी नंबरवरून कॉल आला होता, त्याची एकदा तपासणी करायला हवी.",
              "intro_green": "एका अनोळखी नंबरवरून कॉल आला होता, तो सुरक्षित वाटला.",
              "spoke": "कॉल करणारे {lang} मध्ये बोलत होते, म्हणून मीही {lang} मध्ये उत्तर दिले.",
              "credentials": "त्यांनी ओटीपी किंवा बँकेची माहिती मागितली.", "authority": "त्यांनी स्वतःला पोलीस किंवा सरकारी अधिकारी सांगितले.",
              "urgency": "त्यांनी धमकी दिली आणि घाई केली.", "secrecy": "त्यांनी कोणालाही न सांगायला सांगितले.", "money": "त्यांनी पैसे मागितले.",
              "remote_access": "त्यांनी एक ॲप डाउनलोड करायला सांगितले.", "family_emergency": "त्यांनी कुटुंबात काहीतरी आणीबाणी असल्याचे सांगितले.",
              "unverified": "त्यांनी स्वतःला कुटुंबातील असल्याचे सांगितले.",
              "action_red": "मी कॉल नम्रपणे संपवला. बाबांशी बोलणे करून दिले नाही आणि कोणतीही माहिती दिली नाही.",
              "action_yellow": "मी संदेश घेतला आहे. कृपया एकदा पाहून घ्या.",
              "action_family": "कृपया तुमच्याकडे आधीपासून असलेल्या नंबरवर फोन करून खात्री करा.",
              "action_green": "मी त्यांचा संदेश घेतला आहे, आणि बाबांना वाचून दाखवू शकते."},
    "bn-IN": {"intro_red": "একটি অচেনা নম্বর থেকে একটি সন্দেহজনক কল এসেছিল।", "intro_yellow": "একটি অচেনা নম্বর থেকে কল এসেছিল, একবার যাচাই করা দরকার।",
              "intro_green": "একটি অচেনা নম্বর থেকে কল এসেছিল, সেটি নিরাপদ মনে হয়েছে।",
              "spoke": "যিনি ফোন করেছিলেন তিনি {lang}-তে কথা বলছিলেন, তাই আমিও {lang}-তে উত্তর দিয়েছি।",
              "credentials": "তিনি ওটিপি বা ব্যাংকের তথ্য চেয়েছিলেন।", "authority": "তিনি নিজেকে পুলিশ বা সরকারি অফিসার বলে দাবি করেছিলেন।",
              "urgency": "তিনি ভয় দেখিয়ে তাড়াহুড়ো করছিলেন।", "secrecy": "তিনি কাউকে না জানাতে বলেছিলেন।", "money": "তিনি টাকা চেয়েছিলেন।",
              "remote_access": "তিনি একটি অ্যাপ ডাউনলোড করতে বলেছিলেন।", "family_emergency": "তিনি পরিবারে জরুরি অবস্থার কথা বলেছিলেন।",
              "unverified": "তিনি নিজেকে পরিবারের লোক বলে দাবি করেছিলেন।",
              "action_red": "আমি ভদ্রভাবে কলটি শেষ করেছি। বাবার সঙ্গে কথা বলাইনি, কোনো তথ্যও দিইনি।",
              "action_yellow": "আমি বার্তাটি নিয়ে রেখেছি। অনুগ্রহ করে একবার দেখে নিন।",
              "action_family": "অনুগ্রহ করে আপনার কাছে আগে থেকে থাকা নম্বরে ফোন করে যাচাই করুন।",
              "action_green": "আমি তাঁর বার্তা নিয়ে রেখেছি, বাবাকে পড়ে শোনাতে পারি।"},
}

_REASON_ORDER = ["authority", "credentials", "money", "urgency", "secrecy", "remote_access", "family_emergency"]


def call_summary(risk: dict, caller_lang: str, family_lang: str) -> str:
    """Gena's spoken summary of a finished call, in the family's language."""
    fl = family_lang if family_lang in SUMMARY else DEFAULT
    S = SUMMARY[fl]
    verdict = risk.get("verdict", "green")
    parts = [S.get("intro_" + verdict, S["intro_green"])]
    if caller_lang and caller_lang != fl and caller_lang in LANG_LATIN:
        parts.append(S["spoke"].format(lang=LANG_LATIN[caller_lang]))
    if risk.get("verify_by_callback"):
        parts.append(S["unverified"])
    cats = [c for c in _REASON_ORDER if c in risk.get("categories", [])]
    parts += [S[c] for c in cats[:4]]
    if verdict == "red":
        parts.append(S["action_red"])
        if risk.get("verify_by_callback"):
            parts.append(S["action_family"])
    elif verdict == "yellow":
        parts.append(S["action_family"] if risk.get("verify_by_callback") else S["action_yellow"])
    else:
        parts.append(S["action_green"])
    return " ".join(parts)
