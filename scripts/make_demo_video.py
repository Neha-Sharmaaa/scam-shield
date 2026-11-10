"""Record the ~60 s "how it works" demo video from the REAL running app.

What it does:
  * opens /static/record.html (caller phone + family dashboard side by side, caption bar)
  * plays three scripted, synthetic calls. The caller's voice is Gnani Timbre audio fed through
    the same 8 kHz phone path into Gnani Prisma as a live mic (window.__demoSay in caller.html)
  * records the screen with Playwright, then builds a soundtrack from the logged audio events
    (assistant voice, caller voice, Kannada message, narration) and muxes an H.264 MP4

Usage (server must be running on :8000):
  .venv/bin/python scripts/make_demo_video.py
Output: static/media/scam-shield-demo.mp4 (+ poster .jpg). Clears the demo call log.
Needs: pip install playwright imageio-ffmpeg (dev-only), Google Chrome.
"""
import asyncio
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import imageio_ffmpeg
import numpy as np
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import audio, gnani  # noqa: E402

B = "http://localhost:8000"
OUT = ROOT / "static" / "media"
SR = 16000

CALLER = {
    "cbi": "Main CBI se bol raha hoon, aapke naam pe case hai, OTP batao.",
    "rel1": "Aunty, Rohit ka accident ho gaya, turant paise bhejo.",
    "rel2": "Main uska dost hoon, jaldi karo!",
    "del1": "Main Suresh bol raha hoon.",
    "del2": "Delivery company se.",
    "del3": "Parcel delivery hai, kal aaunga, ghar pe koi hoga?",
}
NARRATION = {
    "n2": "Scam calls target our parents every day. Scam Shield answers them first. Here's how.",
    "n3": "Unknown callers never reach Papa directly. Scam Shield. Built on Gnani Prisma and Timbre.",
}


async def prepare():
    caller, narr = {}, {}
    for k, t in CALLER.items():
        p = await gnani.synthesize(t, language="hi-en", voice=gnani.CALLER_VOICE, sample_rate=SR, speed=1.0)
        caller[k] = (f"/api/audio/{p.name}", p)
    for k, t in NARRATION.items():
        narr[k] = await gnani.synthesize(t, language="en-IN", voice=gnani.AGENT_VOICE, sample_rate=SR, speed=1.0)
    return caller, narr


def dur(path: Path) -> float:
    x, sr = audio.read_wav(path.read_bytes())
    return len(x) / sr


async def run(caller, narr, workdir: Path):
    events = []          # (absolute_time_s, wav_path)
    marks = {}           # scene start times (absolute), used to cut one clip per case
    t0 = None
    async with httpx.AsyncClient(base_url=B, timeout=60) as c:
        await c.delete("/api/calls")
        await c.post("/api/settings", json={"parent_name": "Sharma ji", "parent_language": "kn-IN", "code_word_enabled": False,
                                           "code_word": "gulmohar", "family_names": ["Priya"], "allow_list": ["Rohit: +91 00000 20002"]})
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=True, args=[
            "--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
        ctx = await b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        pg = await ctx.new_page()
        await pg.goto(B + "/static/record.html")
        await pg.evaluate("showCard('', '')")
        await pg.evaluate("document.getElementById('dash').src = '/dashboard?embed=1'")
        await asyncio.sleep(1.5)

        # capture: screenshot loop (~12 fps); crisp full frames with exact timestamps
        frames, recording = [], True

        async def grab():
            while recording:
                t = time.time()
                frames.append((t, await pg.screenshot(type="jpeg", quality=90)))
                await asyncio.sleep(max(0.0, 1 / 12 - (time.time() - t)))
        grabber = asyncio.create_task(grab())
        await asyncio.sleep(0.3)

        async def frame(sel):
            return await (await pg.query_selector(sel)).content_frame()

        async def cap(n, html, who="shieldy", mood="happy"):
            await pg.evaluate("([n, h, w, m]) => setCap(n, h, w, m)", [n, html, who, mood])

        async def card(h, p_, chips, key, hold, story=None):
            await pg.evaluate("([h, p, c, s]) => showCard(h, p, c, s)", [h, p_, chips, story])
            events.append((time.time(), narr[key]))
            await asyncio.sleep(max(hold, dur(narr[key]) + 0.6))

        async def collect(fr):
            for e in await fr.evaluate("window.__events || []"):
                path = gnani.TTS_CACHE / e["url"].split("/")[-1]
                events.append((e["t"] / 1000.0, path))

        async def say(fr, key):
            n = await fr.locator(".bubble.caller").count()
            await fr.evaluate("(u) => { window.__p = window.__demoSay(u); }", caller[key][0])
            await fr.wait_for_function(f"document.querySelectorAll('.bubble.caller').length > {n}", timeout=60000)

        async def wait_turn(fr):
            await fr.wait_for_function("!document.getElementById('micBtn').disabled || getComputedStyle(document.getElementById('againBtn')).display !== 'none'", timeout=60000)

        async def wait_done(fr):
            await fr.wait_for_function("getComputedStyle(document.getElementById('againBtn')).display !== 'none' && document.getElementById('status').textContent.includes('📴')", timeout=60000)

        async def fresh_dashboard():
            """Each clip stands alone: clear the call log and reload the dashboard between cases."""
            async with httpx.AsyncClient(base_url=B, timeout=30) as hc:
                await hc.delete("/api/calls")
            await pg.evaluate("(() => { const f = document.getElementById('dash'); f.src = '/dashboard?embed=1&r=' + Date.now(); })()")
            await asyncio.sleep(2.0)

        async def start_call(number):
            await pg.evaluate("(u) => { document.getElementById('caller').src = u; }", "/caller?n=" + number.replace("+", "%2B").replace(" ", "%20"))
            await asyncio.sleep(1.2)
            fr = await frame("#caller")
            await fr.wait_for_selector("#startBtn")
            await fr.click("#startBtn")
            return fr

        # --- intro (one card)
        await card("Scam Shield answers unknown calls <em>before Papa does</em>.",
                   "Fake police. Fake “relatives”. “Tell me the OTP.” Here's how it stops them.",
                   ["🎙️ Gnani Prisma", "🔊 Gnani Timbre", "📶 8 kHz phone audio"], "n2", 5.2, story="intro")
        await cap("1", "A fake CBI officer calls Papa <small>…but the AI assistant picks up instead</small>", "scammer", "smirk")
        await pg.evaluate("hideCard()")
        await asyncio.sleep(0.7)            # let the card fade out before the clip starts
        marks["cbi"] = time.time()

        # --- scene 1: fake CBI
        fr = await start_call("+91 00000 10001")
        await wait_turn(fr)
        await cap("1", "He starts the “digital arrest” script <small>Gnani Prisma transcribes him from 8 kHz phone-line audio</small>", "scammer", "talk")
        await say(fr, "cbi")
        await cap("1", "🔴 CBI + threat + OTP request → call ended <small>Papa is never connected. The family gets an instant alert, with reasons.</small>", "scammer", "angry")
        await wait_done(fr)
        await asyncio.sleep(2.2)
        await collect(fr)

        # --- scene 2: fake relative
        marks["cbi_end"] = time.time()
        await fresh_dashboard()
        marks["relative"] = time.time()
        await cap("2", "A “relative in trouble” calls from a new number <small>…the most emotional scam of all</small>", "scammer", "talk")
        fr = await start_call("+91 00000 10002")
        await wait_turn(fr)
        await say(fr, "rel1")
        await cap("2", "Family claim + panic + money = the classic scam <small>The assistant asks who they are, and never hands over the phone</small>", "shieldy", "alert")
        await wait_turn(fr)
        await say(fr, "rel2")
        await wait_done(fr)
        dash = await frame("#dash")
        await dash.evaluate("document.querySelector('.verify')?.scrollIntoView({block: 'center', behavior: 'smooth'})")
        await cap("2", "🔴 Stopped. You're told to call Rohit back <small>on the number you already have, not the one that called</small>", "scammer", "sad")
        await asyncio.sleep(3.2)
        await collect(fr)

        # --- scene 3: genuine delivery
        marks["relative_end"] = time.time()
        await fresh_dashboard()
        dash = await frame("#dash")
        marks["delivery"] = time.time()
        await cap("3", "A genuine delivery call <small>Real callers just answer three quick questions</small>", "shieldy", "happy")
        fr = await start_call("+91 00000 10003")
        for k in ("del1", "del2", "del3"):
            await wait_turn(fr)
            await say(fr, k)
        await wait_done(fr)
        await collect(fr)
        await cap("3", "🟢 Safe. Message taken <small>Gnani Timbre reads it to Papa in his own language: Kannada</small>", "papa", "happy")
        await dash.evaluate("document.querySelector('[data-play]')?.scrollIntoView({block: 'center', behavior: 'smooth'})")
        await asyncio.sleep(1.0)
        await dash.click("[data-play]")
        await dash.wait_for_function("(document.querySelector('.caption.on')?.textContent || '').startsWith('✓')", timeout=60000)
        await asyncio.sleep(0.8)
        await collect(dash)

        # --- outro
        marks["outro"] = time.time()
        await card("Unknown callers never reach Papa <em>directly</em>.",
                   "Scam Shield flags suspicious calls · Built on Gnani Prisma + Timbre",
                   ["▶ Try it: place a test call", "🛡️ Open the family dashboard"], "n3", 4.8, story="outro")
        recording = False
        await grabber
        t_end = time.time()
        await ctx.close()
        await b.close()
    t0 = frames[0][0]
    for i, (t, jpg) in enumerate(frames):
        (workdir / f"f{i:05d}.jpg").write_bytes(jpg)
    lines = []
    for i, (t, _) in enumerate(frames):
        nxt = frames[i + 1][0] if i + 1 < len(frames) else t_end
        lines += [f"file 'f{i:05d}.jpg'", f"duration {max(0.01, nxt - t):.4f}"]
    lines.append(f"file 'f{len(frames) - 1:05d}.jpg'")
    (workdir / "frames.txt").write_text("\n".join(lines))
    webm = workdir / "frames.txt"
    async with httpx.AsyncClient(base_url=B, timeout=60) as c:
        await c.delete("/api/calls")
    return t0, t_end, webm, events, marks


def soundtrack(t0, t_end, events, path: Path):
    total = np.zeros(int((t_end - t0 + 1) * SR), dtype=np.float32)
    for t, wav in events:
        x, sr = audio.read_wav(Path(wav).read_bytes())
        if sr != SR:
            x = np.interp(np.linspace(0, len(x) - 1, int(len(x) * SR / sr)), np.arange(len(x)), x).astype(np.float32)
        i = max(0, int((t - t0) * SR))
        j = min(len(total), i + len(x))
        total[i:j] += x[: j - i]
    peak = float(np.max(np.abs(total))) or 1.0
    total *= min(1.0, 0.95 / peak)
    path.write_bytes(audio.write_wav(total, SR))


SPEED = 1.15   # final video plays 15% faster (pitch-preserving atempo for the audio)


def mux(frames_list: Path, wav: Path, out: Path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(frames_list), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a",
                    "-vf", f"setpts=PTS/{SPEED},fps=25,format=yuv420p", "-af", f"atempo={SPEED},aresample=44100",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", "3.8", "-i", str(out), "-frames:v", "1", "-q:v", "3",
                    str(out.with_suffix(".jpg"))], check=True)


def cut(src: Path, start: float, end: float, out: Path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    d = end - start
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{d:.3f}",
                    "-vf", "fade=t=in:st=0:d=0.25", "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={max(0, d - 0.4):.3f}:d=0.4",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-ss", "1.2", "-i", str(out), "-frames:v", "1", "-q:v", "3",
                    str(out.with_suffix(".jpg"))], check=True)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    caller, narr = await prepare()
    work = Path(tempfile.mkdtemp(prefix="ssdemo_"))
    t0, t_end, webm, events, marks = await run(caller, narr, work)
    wav = work / "track.wav"
    soundtrack(t0, t_end, events, wav)
    out = OUT / "scam-shield-demo.mp4"
    mux(webm, wav, out)
    print(f"full video: {out} ({out.stat().st_size / 1e6:.1f} MB, {(t_end - t0) / SPEED:.1f} s, {len(events)} audio events)")
    # one short clip per case, for the home page picker
    vt = {k: (v - t0) / SPEED for k, v in marks.items()}
    for name, a, b in (("cbi", "cbi", "cbi_end"), ("relative", "relative", "relative_end"), ("delivery", "delivery", "outro")):
        clip = OUT / f"case-{name}.mp4"
        cut(out, vt[a], vt[b], clip)
        print(f"clip {clip.name}: {vt[b] - vt[a]:.1f} s, {clip.stat().st_size / 1e6:.1f} MB")
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
