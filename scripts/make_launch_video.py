"""LinkedIn launch video (4:5, 1080x1350): announces Scam Shield + Gena, with a REAL multilingual case.

Story: hook -> scam scripts -> "So I built Scam Shield. Meet Gena." -> how she protects Papa ->
English scammer calls a Hindi family (Gena switches to English, 🔴) ->
Tamil + Bengali callers (Gena replies in each) -> English courier's message read to Papa in Hindi ->
safe-when-wrong -> end card with the live link.

The multilingual chats replay real calls captured by running Timbre caller audio -> 8 kHz -> Prisma ->
Gena on the local server (data/launch/script.json; see the README for how it was produced).

Usage (server on :8000): .venv/bin/python scripts/make_launch_video.py
Output: static/media/scam-shield-launch.mp4 (+ .jpg)
"""
import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from app import audio, gnani  # noqa: E402
from make_linkedin_video import FF, MEDIA, SR, W, H, B, clip_audio, media_dur, ring_wav, wav_dur  # noqa: E402

SPEED = 1.15   # final video plays 15% faster (pitch-preserving)
LAUNCH = json.loads((ROOT / "data" / "launch" / "script.json").read_text())

NARRATION = {
    "n1": "Every day, scammers call our parents.",
    "n2": "Fake police. Fake relatives. Fake bank calls. Every script runs on panic.",
    "n3": "So I built Scam Shield. Meet जीना. She answers unknown calls before Papa does, spots the scam script, and alerts the family.",
    "s1": "Gena answers first, and asks who's calling, and why.",
    "s2": "She spots the scam script. O T P requests, police threats, secrecy, money.",
    "s3": "Scam calls end politely, and the family gets an alert.",
    "s4": "Safe messages are read to Papa, in his own language.",
    "m1": "But what if the scammer speaks English?",
    "m2": "Tamil, Telugu, Bengali... जीना replies in whatever language the caller speaks.",
    "m4": "Then जीना tells the family what happened, in their own language.",
    "m3": "And Papa always hears the message in his own language.",
    "n5": "And if it's ever unsure, a genuine caller just leaves a message.",
    "n6": "Scam Shield. Built on Gnani Prisma and Timbre. Try it live. The link is in the post.",
}
LANG_NAME = {"en-IN": "English", "hi-IN": "हिन्दी", "ta-IN": "தமிழ்", "bn-IN": "বাংলা", "kn-IN": "ಕನ್ನಡ", "te-IN": "తెలుగు", "mr-IN": "मराठी"}
LANG_EN = {"en-IN": "English", "hi-IN": "Hindi", "ta-IN": "Tamil", "bn-IN": "Bengali", "kn-IN": "Kannada", "te-IN": "Telugu", "mr-IN": "Marathi"}


async def main():
    work = Path(tempfile.mkdtemp(prefix="sslaunch_"))
    narr = {k: await gnani.synthesize(t, language="en-IN", voice=gnani.AGENT_VOICE, sample_rate=SR, speed=1.08)
            for k, t in NARRATION.items()}
    ring = work / "ring.wav"; ring_wav(ring)

    events = []
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": W, "height": H})).new_page()
        await pg.goto(B + "/static/linkedin.html")
        await asyncio.sleep(1.5)
        frames, rec = [], True

        async def grab():
            while rec:
                t = time.time()
                frames.append((t, await pg.screenshot(type="jpeg", quality=88)))
                await asyncio.sleep(max(0.0, 1 / 14 - (time.time() - t)))
        task = asyncio.create_task(grab())

        async def say(key, delay=0.0):
            if delay:
                await asyncio.sleep(delay)
            events.append((time.time(), narr[key]))
            return wav_dur(narr[key])

        async def play(path):
            events.append((time.time(), Path(path)))
            return wav_dur(Path(path))

        async def scene(name, progress):
            await pg.evaluate("([n, p]) => go(n, p)", [name, progress])

        async def chat(items, skip_greeting_audio=False):
            """Replay a real call: bubbles appear as each voice plays; the chip flags language switches."""
            current = "hi-IN"
            for i, it in enumerate(items):
                if it["who"] == "gena":
                    code = next((k for k, v in LANG_NAME.items() if v == it["lang"]), "hi-IN")
                    if code != current:
                        await pg.evaluate("l => chatLang(l)", f"Gena switched to {it['lang']}")
                        await asyncio.sleep(0.5); current = code
                    await pg.evaluate("a => chatAdd(...a)", ["gena", f"Gena · {it['lang']}", it["text"], it["sub"] if it["sub"] != it["text"] else ""])
                    if i == 0 and skip_greeting_audio:
                        await asyncio.sleep(1.0)
                    else:
                        d = await play(it["audio"]); await asyncio.sleep(d + 0.25)
                elif it["who"] == "caller":
                    lang = LANG_EN.get(it["lang"], it["lang"])
                    await pg.evaluate("a => chatAdd(...a)", ["caller", f"Caller · {lang} (detected by Gnani Prisma)", it["text"], ""])
                    d = await play(it["audio"]); await asyncio.sleep(d + 0.25)
                elif it["who"] == "verdict":
                    txt = "🔴 High risk · " + " + ".join(it["reasons"][:3]) + " → call ended" if it["verdict"] == "red" else "🟢 Safe · message taken"
                    await pg.evaluate("a => chatAdd(...a)", ["verdict" + ("" if it["verdict"] == "red" else " green"), "", txt, ""])
                    await asyncio.sleep(1.8)

        # 1. hook
        await scene("hook", 6); events.append((time.time(), ring))
        d = await say("n1", 1.0); await asyncio.sleep(d + 0.5)
        # 2. scripts
        await scene("scripts", 14)
        d = await say("n2", 0.3)
        for i in range(1, 5):
            await pg.evaluate(f"bubble({i})"); await asyncio.sleep(0.6)
        await asyncio.sleep(max(0.3, d - 2.4 + 0.3))
        # 3. meet Gena
        await scene("meet", 24)
        d = await say("n3", 0.5); await asyncio.sleep(d + 0.3)
        # 6. multilingual: English scammer -> Hindi family
        await scene("multi", 40)
        await pg.evaluate("a => chatReset(...a)", ["A scammer calls a Hindi family <em>in English.</em>", "Unknown caller · +91 00000 40001", "Gena speaks हिन्दी"])
        d = await say("m1", 0.2); await asyncio.sleep(d)
        await chat(LAUNCH["english"])
        # 6b. family dashboard: Gena's spoken summary (real, family language)
        sm = LAUNCH["summary"]
        await scene("dash", 58)
        await pg.evaluate("a => dashSummary(...a)", [sm["number"], " + ".join(sm["reasons"]),
                          f"🗣 Caller spoke {LANG_EN.get(sm['caller_lang'], '')} · Gena replied in {LANG_EN.get(sm['reply_lang'], '')}",
                          sm["text"], LANG_NAME[sm["lang"]]])
        d = await say("m4", 0.3); await asyncio.sleep(d + 0.15)
        d = await play(sm["audio"]); await asyncio.sleep(d + 0.5)
        # 7. Tamil (Gena replies in the caller's language)
        await scene("multi", 70)
        await pg.evaluate("a => chatReset(...a)", ["Tamil? Telugu? Bengali? Gena replies <em>in the caller's language.</em>", "Unknown caller · +91 00000 40002", "Gena speaks हिन्दी"])
        d = await say("m2", 0.2); await asyncio.sleep(max(0.4, d - 1.2))
        ta, bn = LAUNCH["tamil"], LAUNCH["bengali"]
        await chat(ta, skip_greeting_audio=True)
        await asyncio.sleep(0.6)
        # 8. Papa hears his own language
        await scene("papa", 84)
        courier_msg = [it for it in LAUNCH["courier"] if it["who"] == "caller"][-1]["text"]
        await pg.evaluate("a => papaRelay(...a)", [courier_msg, LAUNCH["relay"]["text"], LANG_NAME[LAUNCH["relay"]["lang"]]])
        d = await say("m3", 0.4); await asyncio.sleep(d + 0.2)
        d = await play(LAUNCH["relay"]["audio"]); await asyncio.sleep(d + 0.4)
        # 10. end card + live link
        await scene("end", 100); await pg.evaluate("showLink()")
        d = await say("n6", 0.4); await asyncio.sleep(d + 1.6)

        rec = False
        await task
        t_end = time.time()
        await b.close()

    t0 = frames[0][0]
    lines = []
    for i, (t, jpg) in enumerate(frames):
        (work / f"f{i:05d}.jpg").write_bytes(jpg)
        nxt = frames[i + 1][0] if i + 1 < len(frames) else t_end
        lines += [f"file 'f{i:05d}.jpg'", f"duration {max(0.01, nxt - t):.4f}"]
    lines.append(f"file 'f{len(frames) - 1:05d}.jpg'")
    (work / "frames.txt").write_text("\n".join(lines))

    total = np.zeros(int((t_end - t0 + 1) * SR), dtype=np.float32)
    for t, wav in events:
        x, sr = audio.read_wav(Path(wav).read_bytes())
        if sr != SR:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x).astype(np.float32)
        i = max(0, int((t - t0) * SR)); j = min(len(total), i + len(x))
        total[i:j] += x[: j - i]
    total *= min(1.0, 0.95 / (float(np.max(np.abs(total))) or 1.0))
    (work / "track.wav").write_bytes(audio.write_wav(total, SR))

    out = MEDIA / "scam-shield-launch.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(work / "frames.txt"),
                    "-i", str(work / "track.wav"), "-map", "0:v", "-map", "1:a",
                    "-vf", f"setpts=PTS/{SPEED},fps=25,format=yuv420p", "-af", f"atempo={SPEED},aresample=44100",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "8", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    str(out.with_suffix(".jpg"))], check=True)
    print(f"launch video: {out} ({out.stat().st_size / 1e6:.1f} MB, {(t_end - t0) / SPEED:.1f} s, {len(frames)} frames)")


if __name__ == "__main__":
    asyncio.run(main())
