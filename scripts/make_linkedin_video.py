"""Record the ~60 s LinkedIn video (4:5, 1080x1350) about how Scam Shield helps elderly parents.

Story: hook -> the scam scripts -> meet Scam Shield -> how it protects Papa -> REAL app footage
(fake CBI call + Kannada message, from static/media/case-*.mp4) -> safe-when-wrong -> end card.
Narration is Gnani Timbre; the footage keeps its real call audio; a synthesized phone ring opens it.

Usage (server running on :8000, case clips already made by make_demo_video.py):
  .venv/bin/python scripts/make_linkedin_video.py
Output: static/media/scam-shield-linkedin.mp4 (+ .jpg thumbnail)
"""
import asyncio
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import audio, gnani  # noqa: E402

B = "http://localhost:8000"
MEDIA = ROOT / "static" / "media"
SR = 16000
W, H = 1080, 1350
FF = imageio_ffmpeg.get_ffmpeg_exe()

NARRATION = {
    "n1": "Every day, scammers call our parents.",
    "n2": "Fake police. Fake relatives. Fake bank calls. Every script runs on panic.",
    "n3": "Meet Scam Shield. An AI assistant that answers unknown calls, before Papa does.",
    "s1": "It answers first, and asks who's calling, and why.",
    "s2": "It spots the scam script. O T P requests, police threats, secrecy, money.",
    "s3": "Scam calls end politely, and the family gets an alert.",
    "s4": "Safe messages are read to Papa, in his own language.",
    "n5": "And if it's ever unsure, a genuine caller just leaves a message.",
    "n6": "Scam Shield. Built on Gnani Prisma and Timbre. So our parents never face scammers alone.",
}


def wav_dur(p: Path) -> float:
    x, sr = audio.read_wav(p.read_bytes())
    return len(x) / sr


def ring_wav(path: Path):
    """Classic two-tone 'tring-tring' phone ring (synthesized, no external assets)."""
    t = np.arange(int(SR * 3.2)) / SR
    tone = 0.5 * np.sin(2 * np.pi * 400 * t) + 0.5 * np.sin(2 * np.pi * 450 * t)
    gate = np.zeros_like(t)
    for start in (0.0, 0.6, 1.8, 2.4):
        gate[(t >= start) & (t < start + 0.4)] = 1.0
    env = np.convolve(gate, np.ones(160) / 160, mode="same")
    path.write_bytes(audio.write_wav((0.22 * tone * env).astype(np.float32), SR))


def clip_audio(mp4: Path, start: float, dur: float, out: Path):
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(mp4), "-t", f"{dur:.3f}",
                    "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], check=True)


def media_dur(mp4: Path) -> float:
    r = subprocess.run([FF, "-hide_banner", "-i", str(mp4)], capture_output=True, text=True)
    h, m, s = r.stderr.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main():
    work = Path(tempfile.mkdtemp(prefix="sslinkedin_"))
    narr = {k: await gnani.synthesize(t, language="en-IN", voice=gnani.AGENT_VOICE, sample_rate=SR, speed=1.08)
            for k, t in NARRATION.items()}
    ring = work / "ring.wav"; ring_wav(ring)
    cbi_mp4, del_mp4 = MEDIA / "case-cbi.mp4", MEDIA / "case-delivery.mp4"
    cbi_start = 4.0                      # skip the greeting: start as the scammer talks
    cbi_len = media_dur(cbi_mp4) - cbi_start
    del_len = 8.5                        # the Kannada message at the end
    del_start = media_dur(del_mp4) - del_len
    clip_audio(cbi_mp4, cbi_start, cbi_len, work / "cbi.wav")
    clip_audio(del_mp4, del_start, del_len, work / "del.wav")

    events = []                      # (absolute time, wav path)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        pg = await (await b.new_context(viewport={"width": W, "height": H})).new_page()
        await pg.goto(B + "/static/linkedin.html")
        await asyncio.sleep(1.5)     # fonts + characters

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

        async def scene(name, progress):
            await pg.evaluate("([n, p]) => go(n, p)", [name, progress])

        # 1. hook: phone rings for Papa
        await scene("hook", 7)
        events.append((time.time(), ring))
        d = await say("n1", 1.0)
        await asyncio.sleep(d + 0.6)

        # 2. the scam scripts
        await scene("scripts", 20)
        d = await say("n2", 0.3)
        for i in range(1, 5):
            await pg.evaluate(f"bubble({i})"); await asyncio.sleep(0.65)
        await asyncio.sleep(max(0.4, d - 2.6 + 0.3))

        # 3. meet Scam Shield
        await scene("meet", 32)
        d = await say("n3", 0.6)
        await asyncio.sleep(d + 0.4)

        # 4. how it protects (one step per narration line)
        await scene("steps", 46)
        await asyncio.sleep(0.3)
        for i, k in enumerate(("s1", "s2", "s3", "s4"), 1):
            await pg.evaluate(f"step({i})")
            d = await say(k, 0.1)
            await asyncio.sleep(d + 0.15)
        await asyncio.sleep(0.3)

        # 5. proof: real app footage, with its real call audio
        await scene("proof", 60)
        t = await pg.evaluate("([s, st, tag, h, sub]) => footage(s, st, tag, h, sub)",
                              ["/static/media/case-cbi.mp4", cbi_start, "● Real demo",
                               "A fake CBI call, <em>stopped in seconds.</em>",
                               "Gnani Prisma transcribes the caller from 8 kHz phone-line audio."])
        events.append((t / 1000.0, work / "cbi.wav"))
        await asyncio.sleep(cbi_len - 0.2)
        await pg.evaluate("stopFootage()")
        await pg.evaluate("go('proof', 74)")
        t = await pg.evaluate("([s, st, tag, h, sub]) => footage(s, st, tag, h, sub)",
                              ["/static/media/case-delivery.mp4", del_start, "● Real demo",
                               "A genuine delivery, <em>read to Papa in Kannada.</em>",
                               "Gnani Timbre speaks the message in his own language."])
        events.append((t / 1000.0, work / "del.wav"))
        await asyncio.sleep(del_len - 0.3)
        await pg.evaluate("stopFootage()")

        # 6. safe when wrong
        await scene("safe", 88)
        d = await say("n5", 0.4)
        await asyncio.sleep(d + 0.9)

        # 7. end card
        await scene("end", 100)
        d = await say("n6", 0.5)
        await asyncio.sleep(d + 1.4)

        rec = False
        await task
        t_end = time.time()
        await b.close()

    # frames -> concat list with real durations
    t0 = frames[0][0]
    lines = []
    for i, (t, jpg) in enumerate(frames):
        (work / f"f{i:05d}.jpg").write_bytes(jpg)
        nxt = frames[i + 1][0] if i + 1 < len(frames) else t_end
        lines += [f"file 'f{i:05d}.jpg'", f"duration {max(0.01, nxt - t):.4f}"]
    lines.append(f"file 'f{len(frames) - 1:05d}.jpg'")
    (work / "frames.txt").write_text("\n".join(lines))

    # soundtrack
    total = np.zeros(int((t_end - t0 + 1) * SR), dtype=np.float32)
    for t, wav in events:
        x, sr = audio.read_wav(Path(wav).read_bytes())
        if sr != SR:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x).astype(np.float32)
        i = max(0, int((t - t0) * SR)); j = min(len(total), i + len(x))
        total[i:j] += x[: j - i]
    total *= min(1.0, 0.95 / (float(np.max(np.abs(total))) or 1.0))
    (work / "track.wav").write_bytes(audio.write_wav(total, SR))

    out = MEDIA / "scam-shield-linkedin.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(work / "frames.txt"),
                    "-i", str(work / "track.wav"), "-map", "0:v", "-map", "1:a",
                    "-vf", "fps=25,format=yuv420p", "-af", "aresample=44100",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", "8", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    str(out.with_suffix(".jpg"))], check=True)
    print(f"LinkedIn video: {out} ({out.stat().st_size / 1e6:.1f} MB, {t_end - t0:.1f} s, {len(frames)} frames)")


if __name__ == "__main__":
    asyncio.run(main())
