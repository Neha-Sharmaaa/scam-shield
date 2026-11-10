# 🛡️ Scam Shield: an AI call guard for elderly parents

Unknown callers never reach the parent directly. A calm assistant (Gnani **Timbre** voice) answers,
asks a few fixed questions, transcribes each answer with Gnani **Prisma** on 8 kHz phone-quality audio,
runs an explainable rule-based risk check, and then either takes a message (🟢), asks the family to call
back (🟡), or ends the call and alerts the son/daughter (🔴).

It **flags suspicious calls**; it does not claim to block every scam. The design is safe when it's
wrong: a genuine caller's worst case is leaving a message.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env            # paste your key from https://app.gnani.ai/voice
.venv/bin/uvicorn app.main:app --port 8000
```

- Home page (start here, links to the demo scenarios): http://localhost:8000/
- Caller simulator (you play the caller): http://localhost:8000/caller
- Family dashboard: http://localhost:8000/dashboard

Open both side by side. Use Chrome and allow the mic. The "No mic? Type the caller's line" box runs the same pipeline
without STT.

The home page shows one short clip per case (`static/media/case-cbi.mp4`, `case-relative.mp4`, `case-delivery.mp4`; the viewer picks which). They are cut from one real recording of the app (`static/media/scam-shield-demo.mp4`, the full version for social posts), made by
`.venv/bin/python scripts/make_demo_video.py` with the server running (dev-only extras: `pip install playwright imageio-ffmpeg`, Google Chrome).
It drives three synthetic calls (Timbre caller voice → 8 kHz → Prisma), burns in captions, and mixes the real audio. It clears the demo call log.

Tests: `.venv/bin/python -m pytest -q` runs the risk check over 47 cases. It is text only and makes no API calls.

## Gnani models and endpoints used

| What | Gnani model | Endpoint |
|---|---|---|
| Caller speech → text (auto-detected: Hinglish, Hindi, English, Kannada, Tamil, Telugu, Marathi, Bengali; 8 kHz mono WAV) | **Prisma v3.0** (`prisma-v3.0`, `language_code=indic-auto`, `format=codemix`) | `POST https://api.vachana.ai/stt/v3` |
| Gena's voice (caller's language) + "message for Papa" (family's language), 7 languages | **Timbre v3.0** (`timbre-v3.0`, voice `Shivani`, all 7 language codes) | `POST https://api.vachana.ai/api/v1/tts/inference` |

Auth is the `X-API-Key-ID` header. The key lives only in `.env` (gitignored) and is used only by the backend
(`app/gnani.py`). It never reaches the browser and is never logged. Every Timbre clip is cached on disk by content hash in
`data/tts_cache/`, and fixed agent lines are pre-rendered at startup, so repeat demos cost no TTS credits. Gnani calls
go through a lock and are retried with backoff on HTTP 429.

## How it works

```
caller mic (48 kHz) ─▶ browser: [optional fan/TV noise] ─▶ 300–3400 Hz band ─▶ 8 kHz mono WAV
        ─▶ FastAPI ─▶ Prisma v3.0 ─▶ transcript ─▶ risk check ─▶ next fixed question (Timbre) or close
                                                         └─▶ dashboard (polling): verdict, reasons, transcript, mock WhatsApp alert
```

- **Fixed script, no LLM** (`app/script.py`): who is calling → which company or department → why. If the caller
  claims to be family (beta, beti, bhaiya, or a name from saved contacts / Settings), "which company" is replaced by
  "what is your relation, and your full name?". The assistant never confirms details, never repeats what was said and
  never accuses anyone. If an answer is empty, the question is re-asked once. The call ends early once the verdict is 🔴,
  but the family question is always asked first when there is a family claim.
- **Family claims are verified by call-back, not by the assistant.** A code word for a 20–30 person Indian family is
  hard to roll out, so it is **optional and off by default**. Instead:
  - family claim + any pressure (money, emergency, urgency, secrecy, credentials, remote access) → 🔴 (this *is* the
    "relative in trouble" script);
  - family claim with no pressure → 🟡 *Unverified family claim*. The caller hears "the family will call you back on the
    number they already have", and the dashboard shows a **📞 Call <name> on saved number** button when the claimed name
    matches a saved contact.
- **Risk check** (`app/risk.py`, phrases in `app/phrases.json`) has seven categories: credentials, authority claim, urgency/threat,
  secrecy, money demand, remote access, and family emergency (which needs a family mention). Phrases are matched in Roman Hinglish,
  Devanagari (as Prisma actually outputs it) and Kannada. A rough Devanagari→Roman transliteration acts as a safety net.
  - 0 categories → 🟢; 1 → 🟡 (or an unverified family claim with no pressure); ≥2, **or** any credentials request,
    **or** an unverified family claim + pressure, **or** a wrong code word (if enabled) → 🔴.
  - Every verdict lists its reasons and the exact phrases that triggered it.
- **Optional code word** (Settings → "Also ask a family code word"), for families whose inner circle will actually use one. It is fuzzy-matched across scripts (`gulmohar` = `गुलमोहर` = noisy `गुलमोहा`). It is deliberately
  **not** sent to Prisma as a keyterm, because biasing STT towards the secret would help a near-miss guess pass.
- **Saved contacts** ("allow-list" in code): numbers already saved on the parent's phone ring straight through; the assistant never answers them. Only unknown numbers are screened, so the family check only ever reaches someone claiming to be family *from a number the family doesn't have*. Saved contacts are written as `Name: number`, and those names also count as family names. In real telephony this list would come from the phone's contacts.
- **"Play message for Papa"** is offered for 🟢 calls only. It uses deterministic Kannada/Hindi templates keyed on the detected benign intent
  (delivery, clinic, neighbour, gas, repair) and time words (aaj/kal/parso), then spoken by Timbre. If no template fits, it plays
  a Kannada intro followed by the caller's own words in Hindi. This is template-based relay, not machine translation.

## Languages: Gena mirrors the caller, the family hears its own language

- **Gena** (the assistant) greets in the household's language (Settings → "Gena greets callers in", default Hindi).
- Prisma runs with `language_code=indic-auto`. After the caller's first answer, Gena **switches to the language they speak** for the rest of the call:
  Hindi/Hinglish, English, Kannada, Tamil, Telugu, Marathi or Bengali (`app/lang.py`). Devanagari text is split into Hindi or Marathi, and Latin text into English or Roman Hinglish.
- Messages for the parent are **always in the family's language** (Settings → "Family's language"). Known intents (delivery, clinic, neighbour, gas, repair, plus today/tomorrow) use templates.
  If the caller spoke a different language and no template fits, Papa is told in his own language that the family will explain. He never hears a language he doesn't speak.
  There is no machine translation; the son/daughter reads the original transcript on the dashboard.
- Scam phrases, family words and intents are listed for every language in `app/phrases.json`. English loanwords such as OTP, police and bank usually come back in Latin script from Prisma `codemix` and are matched in any language.
- Verified on real audio (Timbre caller → 8 kHz → Prisma): an English scammer, a Tamil scammer, a genuine English courier and a genuine Bengali neighbour calling a Hindi-only family.
- Translations are hand-written; have native speakers review each language before real use.

## Verification done (Nov 10)

- Timbre-synthesized caller lines → 8 kHz phone band → Prisma, clean **and** with fan/TV-like noise at ~8 dB SNR
  (`scripts/roundtrip.py`). Real transcripts are saved as test fixtures (`tests/fixtures/prisma_transcripts.json`), and the
  phrase lists were written against them.
- Full calls through the HTTP API with noisy audio (`scripts/e2e_audio.py`): fake CBI → 🔴, fake relative → 🔴, delivery → 🟢.
- Headless Chrome with a fake mic: 48 kHz mic audio is downsampled in-page to 8 kHz, transcribed exactly, and returns 🔴 with reasons.
- The Kannada "message for Papa" audio was sent back through Prisma (`kn-IN`) and came back word for word.
- The API key does not appear in logs, static files, API responses or git.

| Acceptance check | Result |
|---|---|
| 1. "Main CBI se… case hai, OTP batao" | 🔴 Credentials + Authority + Urgency/threat |
| 2. "Aunty, Rohit ka accident… turant paise bhejo" | 🔴 Unverified family claim + Urgency + Money + Family emergency (no code word needed) |
| 3. Family claim with no pressure ("naya number hai") | 🟡 Unverified family claim → call back on saved number; with the optional code word correct → not red |
| 4. "Amazon delivery hai, kal aaunga…" | 🟢; Kannada message: "ಅಪ್ಪಾ, ನಿಮಗೆ ಒಂದು ಕರೆ ಬಂದಿತ್ತು. ನಿಮ್ಮ ಪಾರ್ಸೆಲ್ ಡೆಲಿವರಿ ಬರುತ್ತಿದೆ. ಅವರು ನಾಳೆ ಬರುತ್ತಾರೆ…" |
| 5. "Bijli vibhag se, aaj raat light kat jayegi" | 🔴 Authority + Urgency |
| 6. Checks 1 and 4 with noise through the 8 kHz path | transcripts usable, verdicts unchanged (`scripts/roundtrip.py`, `scripts/e2e_audio.py`) |
| 7. No key in logs, frontend or git | checked |

## Deliberate deviations from the original phrase brief (to avoid false alarms)

- `fine` is matched only as `fine bharo/bharna/lagega` ("I'm fine" and "fine hai" are everyday speech).
- `abhi` is matched only as `abhi ke abhi`, `abhi karo` or `abhi bhejo`, because plain "abhi" appears in almost every sentence.
- `pin` excludes `pin code`, since delivery agents ask for the PIN code. `cash on delivery` is excluded from money demand.
- Added `bijli vibhag` / `बिजली विभाग` / electricity board as an authority claim, so acceptance check 5 reaches 🔴.
- Added legal-threat phrasing (`aapke naam pe case`, `aapke khilaf`) to urgency/threat. On a noisy line Prisma once heard
  "OTP batao" as "बोली भी बता". With this phrase the fake-CBI call still reaches 🔴 from Authority + Threat.
- Prisma `keyterms` with scam vocabulary were A/B tested (`scripts/keyterm_ab.py`). They showed no accuracy gain on noisy clips and
  caused no false positives, so they are left **off**.
- Roman `fir` (Hinglish for "phir") and `thane` (a city) were dropped.

## Deployment (Render + Vercel)

**Live:** website <https://scam-shield-zeta-three.vercel.app> · backend API <https://scam-shield-api-davx.onrender.com/api/health> · code <https://github.com/Neha-Sharmaaa/scam-shield>

Redeploy: pushing to `main` auto-deploys Render. For Vercel, run `scripts/build_vercel.py <render-url>` and then `scripts/deploy_vercel.py`.

- **Backend on Render** (`render.yaml`): a FastAPI web service. `GNANI_API_KEY` is a secret env var set on Render and never committed. `GNANI_DAILY_CAP` (default 400) caps real Gnani requests per day. Each visitor is rate-limited (20 calls/hour), so a public link can't drain credits.
- **Website on Vercel**: `python scripts/build_vercel.py https://<render-url>` builds `.deploy/scam-shield/`, the static pages and media plus a `vercel.json` that **proxies `/api/*` to Render**. The browser talks to one origin, and the key stays on Render.
- The free Render tier sleeps when idle, so the first request after a while takes about 30–60 s. Its disk is temporary: the demo call log resets on restart. Gena's fixed Hindi lines ship pre-rendered in `app/tts_seed/`, so restarts don't spend TTS credits.
- The public dashboard is a shared demo: anyone with the link can see and clear the demo call log and settings. All data is synthetic.

## Limits and next steps

- The call is simulated in the browser. Next step: real telephony (Exotel/Twilio SIP → Prisma realtime WebSocket).
- Kannada phrase lists and message templates were written without a native-speaker review; get one.
- The greeting says "<parent name> ki sahayak", as in the brief. Families can change it in Settings, since naming the
  parent tells a cold caller the surname.
- More languages (Tamil, Telugu) only need entries in `phrases.json`. Scam patterns can be updated without code changes.
- All data is synthetic: numbers use the invalid `+91 00000 …` range, names are made up, and the scam calls are scripted role-play.
