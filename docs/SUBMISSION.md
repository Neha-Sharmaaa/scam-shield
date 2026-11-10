# Submission draft: Great Indian AI Internship Challenge

## Title
**Scam Shield: an AI call guard that answers unknown calls for elderly parents**

## Problem
Phone fraud in India targets elderly people with scripts built on panic: "digital arrest" by fake CBI or police, drugs in a
courier parcel, KYC/bank blocks ("tell me the OTP"), electricity disconnection tonight, a relative in an accident who needs
money now, remote-access apps, and "money sent by mistake". These scripts only work when the scammer can talk to the victim
directly and keep them on the line.

## Solution
Scam Shield sits between unknown callers and the parent, so **unknown callers never reach the parent directly**. A calm assistant called **Gena** answers and asks three fixed questions: who is calling, from which organisation, and why. Each answer is
transcribed from 8 kHz phone-quality audio and checked against explainable rules (credential requests, authority claims,
threats and urgency, secrecy, money demands, remote-access apps, family emergencies). If the caller claims to be family,
the assistant asks for their relation and name, and the family **verifies by calling back on a number they already
have**; a "relative" who adds money, an emergency or secrecy is flagged immediately. (An optional family code word is
available for inner circles.) The call ends in one of three ways:
- 🟢 the message is relayed to the parent in their own language (Kannada or Hindi)
- 🟡 the family calls back
- 🔴 the call is ended politely and the son/daughter gets an alert with the reasons and the full transcript

It doesn't have to catch every scam. A gatekeeper that never hands over the phone takes away the scammer's leverage, and when
it's wrong, a genuine caller just leaves a message.

## Target users
Adult children (often living in another city) of elderly parents who are frequent fraud targets. Also senior-citizen
associations, RWAs and old-age homes.

## Gnani AI models used
- **Prisma v3.0 (speech-to-text)**, `POST /stt/v3`. It auto-detects and transcribes callers in Hinglish, Hindi, English, Kannada, Tamil, Telugu, Marathi and Bengali from
  **8 kHz mono** telephone-band audio. We tested it with simulated fan/TV noise at ~8 dB SNR: the demo calls still got the
  correct verdict. `codemix` output keeps terms like OTP and CBI in Latin script, which suits keyword-based risk checks.
- **Timbre v3.0 (text-to-speech)**, `POST /api/v1/tts/inference`. It is the assistant's Hindi voice (Shivani), and it reads
  relayed messages to the parent in **Kannada** or Hindi.

Awards we're aiming for: Real Deal (fraud on the elderly), Noise Canceller (8 kHz plus noise), Mixed Vibes (Hinglish
code-mix), Main Character (Kannada).

## Team contributions
- _[Name]_: _[e.g. product idea, risk rules, demo video]_
- _[Name]_: _[e.g. backend + Gnani integration, frontend]_

## Next steps
Real telephony (Exotel/Twilio → Prisma realtime streaming), more regional languages, community-updated scam patterns, and
one-tap reporting to 1930 / Chakshu.

*All data is synthetic: phone numbers are invalid by design, names are made up, and scam calls are scripted role-play.*

---

## LinkedIn / X post draft

[Your own opening line, e.g. a real experience in your family, if you have one and are comfortable sharing it.]

Fake CBI officers. "Aapka parcel customs mein pakda gaya." "OTP batao warna account band." 📵 Scam calls like these
target our parents and grandparents every day.

So for the **Great Indian AI Internship Challenge** by **Gnani AI** I built **Scam Shield** 🛡️, an AI call guard that picks up
unknown calls *before* they reach elderly parents.

🎙️ Gena, a calm AI assistant, asks who's calling, from where and why, in the caller's own language (7 Indian languages)
🔎 **Gnani Prisma** transcribes Hinglish/Kannada speech, even on noisy 8 kHz phone audio
🚩 Explainable rules flag OTP requests, "digital arrest" threats, secrecy and money demands
👨‍👩‍👦 Claiming to be family from a new number? You get a nudge to call back on the number you already have
🔊 Safe calls: **Gnani Timbre** reads the message to Papa in the family's own language
📲 Suspicious calls: ended politely, and the family gets an alert with the reasons

It flags suspicious calls rather than claiming to stop every scam. When it gets one wrong, a genuine caller just leaves a message. 🙏

🎥 1-minute video below 👇 (all calls are scripted role-play with synthetic data)

*(Attach `static/media/scam-shield-linkedin.mp4`, 4:5 portrait, captions burned in. LinkedIn uses the first frame as the thumbnail unless you upload `scam-shield-linkedin.jpg` as a custom one.)*

[@-mention Gnani AI: type @Gnani and pick their company page from LinkedIn's dropdown; plain text does not tag]
#GnaniAI #GreatIndianAIInternshipChallenge #VoiceAI #CyberSafety #ElderCare
