"""Drive full screening calls through the running server with *audio*:
Timbre (male caller voice) -> 8 kHz phone band (+noise) -> /api/call/{id}/answer -> Prisma.

Usage: .venv/bin/python scripts/e2e_audio.py [--clean]
Requires the server on localhost:8000.
"""
import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import audio, gnani  # noqa: E402

BASE = "http://localhost:8000"
SCENARIOS = [
    ("+91 00000 10001", "Fake CBI", ["Main CBI officer Verma bol raha hoon.",
                                     "Cyber cell, Delhi se.",
                                     "Aapke naam pe case hai, OTP batao."]),
    ("+91 00000 10002", "Fake relative", ["Aunty, Rohit ka accident ho gaya, turant paise bhejo.",
                                          "Code word? Mujhe yaad nahi, jaldi karo."]),
    ("+91 00000 10003", "Delivery", ["Main Suresh bol raha hoon.",
                                     "Amazon delivery se.",
                                     "Amazon delivery hai, kal aaunga, ghar pe koi hoga?"]),
]


async def caller_wav(text: str, noisy: bool) -> bytes:
    wav = (await gnani.synthesize(text, language="hi-en", voice=gnani.CALLER_VOICE,
                                  sample_rate=16000, speed=1.0)).read_bytes()
    x, sr = audio.read_wav(wav)
    y = audio.to_phone_line(x, sr)
    if noisy:
        y = audio.add_noise(y, 8000, snr_db=8)
    return audio.write_wav(y, 8000)


async def main():
    noisy = "--clean" not in sys.argv
    async with httpx.AsyncClient(base_url=BASE, timeout=120) as c:
        for number, name, lines in SCENARIOS:
            r = (await c.post("/api/call/start", json={"number": number})).json()
            cid = r["call_id"]
            print(f"\n=== {name} ({'noisy' if noisy else 'clean'} 8 kHz)\nAGENT: {r['prompt']['roman']}")
            for line in lines:
                wav = await caller_wav(line, noisy)
                r = await c.post(f"/api/call/{cid}/answer", files={"audio": ("a.wav", wav, "audio/wav")})
                r.raise_for_status()
                r = r.json()
                print(f"CALLER said: {line}\n  Prisma: {r['transcript']}\n  risk: {r['risk']['verdict']} {r['risk']['reasons']}\nAGENT: {r['prompt']['roman']}")
                if r["done"]:
                    break


if __name__ == "__main__":
    asyncio.run(main())
