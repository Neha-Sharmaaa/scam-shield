# Demo video script (~60 s) and synthetic caller lines

**Setup:** server running, `/caller` on the left and `/dashboard` on the right. Settings: parent "Sharma ji", language Kannada,
saved contact `Rohit: +91 00000 20002`, other family names `Priya`, code word **off**. Click **Clear demo call log** first. To show off noise handling,
turn on a fan or TV, or tick "Simulate a noisy line".

Everything below is scripted role-play. The numbers are invalid by design (`+91 00000 …`) and the names are made up.

| Time | On screen | Caller says (tap mic, speak, tap again) |
|---|---|---|
| 0–5 s | Title card / dashboard | **VO:** "Har din hazaron parents ko yeh call aata hai." |
| 5–25 s | Call 1 from `+91 00000 10001` | Assistant greets → **"Main CBI officer Verma bol raha hoon."** → asked department → **"Cyber cell, Delhi se."** → asked purpose → **"Aapke naam pe case hai, OTP batao, kisi ko mat batana."** |
| | | Assistant: "Dhanyavaad. Yeh call samaapt ki ja rahi hai." Dashboard: 🔴 + mock WhatsApp alert: *Authority claim + Urgency/threat + Credentials + Secrecy* |
| 25–40 s | Call 2 from `+91 00000 10002` | **"Aunty, Rohit ka accident ho gaya, turant paise bhejo."** → assistant asks their relation and full name → **"Main uska dost hoon, jaldi karo!"** |
| | | 🔴 *Unverified family claim + Urgency + Money demand + Family emergency*. Dashboard: "Call back on a number you already have" + **📞 Call Rohit on saved number** |
| 40–52 s | Call 3 from `+91 00000 10003` | **"Main Suresh bol raha hoon."** → **"Delivery company se."** → **"Amazon delivery hai, kal aaunga, ghar pe koi hoga?"** → 🟢 |
| | | On the dashboard click **🔊 Play message for Papa** (ಕನ್ನಡ): Timbre speaks in Kannada |
| 52–60 s | End card | "Scam Shield: flags suspicious calls, so Papa never has to. Built on Gnani **Prisma** (STT) + **Timbre** (TTS). #GnaniAI" |

Optional extras if time allows:
- Saved contact `+91 00000 20002` (Rohit): rings straight through; the assistant never picks up.
- Harmless relative: "Main Rohit bol raha hoon, naya number hai" → relation question → "Main uska bhai, bas haal chaal poochna tha" → 🟡 *Unverified family claim*; caller hears "the family will call you back on the number they already have".
- Optional code word: turn it on in Settings (`gulmohar`), repeat the call, answer "gulmohar" → not red.
- Electricity scam: "Bijli vibhag se bol raha hoon" → "Aaj raat light kat jayegi" → 🔴.
- AnyDesk: "Bank se, refund ke liye AnyDesk app download kar lijiye" → 🔴 (Remote access + Money demand).
- Kannada caller: "ನಾನು ಪೊಲೀಸ್ ಠಾಣೆಯಿಂದ, ತಕ್ಷಣ ಹಣ ಕಳುಹಿಸಿ" → 🔴.

Tips: speak right after tapping the mic, pause about half a second before tapping again, and keep each answer under 25 s.
