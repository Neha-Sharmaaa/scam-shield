"""A/B: Prisma with vs without scam-vocabulary keyterms, on noisy 8 kHz caller lines."""
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import audio, gnani, risk
LINES = ["Aapke naam pe case hai, OTP batao.", "Main CBI se bol raha hoon, aapke naam pe case hai, OTP batao.",
         "Amazon delivery hai, kal aaunga, ghar pe koi hoga?", "Main Suresh bol raha hoon.",
         "Doctor clinic se bol rahe hain, aapka appointment kal subah hai.", "AnyDesk app download kar lijiye."]
KT = json.loads((Path(__file__).resolve().parent.parent / "app/phrases.json").read_text())["stt_keyterms"]
async def main():
    for line in LINES:
        wav = (await gnani.synthesize(line, language="hi-en", voice=gnani.CALLER_VOICE, sample_rate=16000, speed=1.0)).read_bytes()
        x, sr = audio.read_wav(wav)
        for seed in (7, 11):
            y = audio.write_wav(audio.add_noise(audio.to_phone_line(x, sr), 8000, snr_db=8, seed=seed), 8000)
            for kt in (None, KT):
                t = (await gnani.transcribe(y, languages="hi-IN,en-IN,kn-IN", keyterms=kt))["transcript"]
                print(f"{'KT ' if kt else '-- '} s{seed} {risk.assess(t)['verdict']:6} {t}")
asyncio.run(main())
