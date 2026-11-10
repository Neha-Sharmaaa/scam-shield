"""Run the real multilingual calls used by the launch video and save data/launch/script.json.

Timbre caller voice -> 8 kHz phone line -> /api/call/{id}/answer (Gnani Prisma, indic-auto) -> Gena.
A Hindi-only family is used; settings are restored afterwards. Server must run on :8000.
"""
import asyncio, json, sys
from pathlib import Path
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import gnani, audio  # noqa: E402

B = "http://localhost:8000"
OUT = Path(__file__).resolve().parent.parent / "data" / "launch"
DEMO = {"parent_name": "Sharma ji", "greeting_language": "hi-IN", "code_word_enabled": False,
        "code_word": "gulmohar", "family_names": ["Priya"], "allow_list": ["Rohit: +91 00000 20002"]}


async def caller_wav(text, lg, name):
    w = (await gnani.synthesize(text, language=lg, voice=gnani.CALLER_VOICE, sample_rate=16000, speed=1.0)).read_bytes()
    x, sr = audio.read_wav(w)
    p = OUT / f"{name}.wav"; p.write_bytes(audio.write_wav(audio.to_phone_line(x, sr), 8000)); return p


def gena(prompt):
    return {"who": "gena", "text": prompt["roman"], "sub": prompt.get("sub", ""), "lang": prompt["lang_name"],
            "audio": str(gnani.TTS_CACHE / prompt["audio_url"].split("/")[-1])}


async def run_call(c, number, lines, name):
    r = (await c.post("/api/call/start", json={"number": number})).json(); cid = r["call_id"]
    items = [gena(r["prompt"])]
    for i, (text, lg) in enumerate(lines):
        wav = await caller_wav(text, lg, f"{name}{i}")
        a = (await c.post(f"/api/call/{cid}/answer", files={"audio": ("a.wav", wav.read_bytes(), "audio/wav")})).json()
        call = next(x for x in (await c.get("/api/calls")).json() if x["id"] == cid)
        items.append({"who": "caller", "text": a["transcript"], "lang": call["turns"][-1].get("spoke"), "audio": str(wav)})
        items.append(gena(a["prompt"]))
        if a["done"]:
            items.append({"who": "verdict", "verdict": a["risk"]["verdict"], "reasons": a["risk"]["reasons"]}); break
    return cid, items


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(base_url=B, timeout=120) as c:
        await c.delete("/api/calls")
        await c.post("/api/settings", json={**DEMO, "parent_language": "hi-IN"})
        out = {}
        en_id, out["english"] = await run_call(c, "+91 00000 40001", [("Hello, this is officer Rao speaking.", "en-IN"),
                                           ("I'm from the CBI. There is a case against you. Tell me the O T P now.", "en-IN")], "en")
        sm = (await c.post(f"/api/calls/{en_id}/summary", json={"language": "hi-IN"})).json()["clips"][0]
        call = next(x for x in (await c.get("/api/calls")).json() if x["id"] == en_id)
        out["summary"] = {"text": sm["text"], "lang": sm["language"], "audio": str(gnani.TTS_CACHE / sm["audio_url"].split("/")[-1]),
                          "number": call["number"], "reasons": call["risk"]["reasons"], "caller_lang": call.get("caller_lang"), "reply_lang": call.get("lang")}
        _, out["tamil"] = await run_call(c, "+91 00000 40002", [("நான் போலீஸ் ஸ்டேஷனில் இருந்து பேசுகிறேன்.", "ta-IN")], "ta")
        _, out["bengali"] = await run_call(c, "+91 00000 40003", [("আমি পাশের বাড়ির রমেশ বলছি।", "bn-IN")], "bn")
        cid, out["courier"] = await run_call(c, "+91 00000 40004", [("Hi, my name is Ravi.", "en-IN"), ("I'm from the courier company.", "en-IN"),
                                             ("I'll deliver your parcel tomorrow. Will someone be at home?", "en-IN")], "co")
        m = (await c.post(f"/api/calls/{cid}/parent_message", json={})).json()["clips"][0]
        out["relay"] = {"text": m["text"], "lang": m["language"], "audio": str(gnani.TTS_CACHE / m["audio_url"].split("/")[-1])}
        (OUT / "script.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
        await c.post("/api/settings", json={**DEMO, "parent_language": "kn-IN"})
        await c.delete("/api/calls")
    for k in ("english", "tamil", "bengali"):
        print(k, "|", " / ".join(f"{i['who']}:{i.get('text', i.get('verdict'))}" for i in out[k])[:230])


if __name__ == "__main__":
    asyncio.run(main())
