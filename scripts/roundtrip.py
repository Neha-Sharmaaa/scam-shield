"""End-to-end check: Timbre speaks synthetic caller lines -> 8 kHz phone line (+noise)
-> Prisma transcribes. Writes tests/fixtures/prisma_transcripts.json.

Usage: .venv/bin/python scripts/roundtrip.py [--fmt codemix|transliterate] [--only N]
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import audio, gnani  # noqa: E402

LINES = [
    ("cbi", "Main CBI se bol raha hoon, aapke naam pe case hai, OTP batao."),
    ("relative", "Aunty, Rohit ka accident ho gaya, turant paise bhejo."),
    ("delivery", "Amazon delivery hai, kal aaunga, ghar pe koi hoga?"),
    ("bijli", "Bijli vibhag se bol raha hoon, aaj raat light kat jayegi."),
    ("codeword", "Code word hai gulmohar."),
]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fmt", default="codemix")
    ap.add_argument("--only", type=int, default=None)
    args = ap.parse_args()
    out_path = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "prisma_transcripts.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    lines = LINES if args.only is None else LINES[args.only:args.only + 1]
    for key, text in lines:
        wav = (await gnani.synthesize(text, language="hi-en", voice=gnani.CALLER_VOICE,
                                      sample_rate=16000, speed=1.0)).read_bytes()
        x, sr = audio.read_wav(wav)
        phone = audio.to_phone_line(x, sr)
        for cond, sig in (("clean_8k", phone), ("noisy_8k", audio.add_noise(phone, 8000, snr_db=8))):
            body = await gnani.transcribe(audio.write_wav(sig, 8000), fmt=args.fmt)
            t = body.get("transcript", "")
            results[f"{key}|{cond}|{args.fmt}"] = {"spoken": text, "transcript": t,
                                                   "lang": body.get("detected_language_code")}
            print(f"[{key:9} {cond:9} {args.fmt}] {t}")
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
