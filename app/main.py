"""Scam Shield backend: FastAPI app that runs the screening call state machine
and proxies Gnani Prisma (STT) + Timbre (TTS) so the API key stays server-side.

Run:  .venv/bin/uvicorn app.main:app --port 8000
"""
import asyncio
import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import gnani, lang, risk, script

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
CALLS_FILE = DATA / "calls.json"
SETTINGS_FILE = DATA / "settings.json"
log = logging.getLogger("scamshield")
logging.basicConfig(level=logging.INFO)

DEFAULT_SETTINGS = {
    "parent_name": "Sharma ji",
    "parent_language": "kn-IN",          # family's language: messages relayed to the parent
    "greeting_language": "hi-IN",        # Gena greets callers in this; then mirrors the caller
    "code_word_enabled": False,           # optional; default is call-back verification
    "code_word": "gulmohar",
    "family_names": ["Rohit", "Priya"],
    "allow_list": ["Rohit: +91 00000 20002"],  # saved contacts; synthetic, invalid-by-design numbers
}
MAX_TURNS = 7

_io_lock = threading.Lock()


def _load(path: Path, default):
    with _io_lock:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return default


def _save(path: Path, obj):
    with _io_lock:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(path)


def get_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    s.update(_load(SETTINGS_FILE, {}))
    return s


def get_calls() -> list:
    return _load(CALLS_FILE, [])


def save_call(call: dict):
    calls = [c for c in get_calls() if c["id"] != call["id"]]
    calls.insert(0, call)
    _save(CALLS_FILE, calls[:200])


def find_call(call_id: str) -> dict:
    for c in get_calls():
        if c["id"] == call_id:
            return c
    raise HTTPException(404, "call not found")


def norm_number(n: str) -> str:
    return "".join(ch for ch in n if ch.isdigit())


def contact_names(allow_list: list) -> list:
    """Names from saved-contact lines like 'Rohit: +91 00000 20002'."""
    out = []
    for line in allow_list:
        if ":" in line:
            name = line.split(":", 1)[0].strip()
            if name and not any(ch.isdigit() for ch in name):
                out.append(name)
    return out


def family_names(s: dict) -> list:
    return list(dict.fromkeys(list(s["family_names"]) + contact_names(s["allow_list"])))


app = FastAPI(title="Scam Shield")


# ------------------------------------------------------------------ public-demo limits
# Per-visitor sliding-window limits (in memory) so a public URL can't drain Gnani credits.
LIMITS = {"start": (20, 3600), "answer": (80, 3600), "relay": (30, 3600), "settings": (30, 3600)}
_hits: dict = {}


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")


def limit(request: Request, kind: str):
    n, window = LIMITS[kind]
    key, now = (client_ip(request), kind), time.time()
    hits = [t for t in _hits.get(key, []) if now - t < window]
    if len(hits) >= n:
        raise HTTPException(429, "Demo limit reached for now. Please try again a little later.")
    hits.append(now)
    _hits[key] = hits


def gnani_error(e: Exception) -> HTTPException:
    msg = str(e)
    return HTTPException(429 if "limit" in msg else 502, msg)


# ------------------------------------------------------------------ TTS helpers

async def tts_url(text: str, language: str = "hi-IN") -> Optional[str]:
    try:
        path = await gnani.synthesize(text, language=language)
        return f"/api/audio/{path.name}"
    except gnani.GnaniError as e:
        log.warning("TTS failed: %s", e)
        return None


@app.get("/api/audio/{name}")
def audio(name: str):
    p = gnani.TTS_CACHE / Path(name).name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="audio/wav")


@app.on_event("startup")
async def prerender():
    """Pre-render all fixed agent lines once (cached on disk) to save credits."""
    seed = ROOT / "app" / "tts_seed"
    if seed.is_dir():
        gnani.TTS_CACHE.mkdir(parents=True, exist_ok=True)
        for f in seed.glob("*.wav"):
            dst = gnani.TTS_CACHE / f.name
            if not dst.exists():
                dst.write_bytes(f.read_bytes())
    if not gnani.has_key():
        log.warning("GNANI_API_KEY missing; add it to .env")
        return

    async def run():
        s = get_settings()
        lg = s.get("greeting_language", lang.DEFAULT)
        L = lang.lines(s["parent_name"], lg)
        for tts, _, _ in L.values():
            await tts_url(tts, lg)
        for step in script.BASE_STEPS + ["codeword", "relation"]:  # "sorry, didn't catch that" + question
            await tts_url(L["reask"][0] + " " + L[step][0], lg)
    asyncio.create_task(run())


# ------------------------------------------------------------------ call flow

def _prompt(call: dict, step: str, reask: bool = False) -> dict:
    """Gena's next line, in the call's current language (the caller's, once detected)."""
    lg = call.get("lang", lang.DEFAULT)
    L = lang.lines(call["parent_name"], lg)
    tts, display, sub = L[step]
    if reask:
        rt, rd, rs = L["reask"]
        tts, display, sub = rt + " " + tts, rd + " " + display, (rs + " " + sub).strip()
    call["last_question"] = display
    return {"step": step, "text": tts, "roman": display, "sub": sub, "lang": lg,
            "lang_name": lang.LANGS[lg][1]}


async def _with_audio(p: dict) -> dict:
    p["audio_url"] = await tts_url(p["text"], p.get("lang", lang.DEFAULT))
    return p


def _caller_text(call: dict) -> str:
    return " ".join(t["transcript"] for t in call["turns"] if t["step"] != "codeword")


def _evaluate(call: dict, settings: dict) -> dict:
    return risk.assess(_caller_text(call), family_names(settings), call["code_word_status"])


class StartBody(BaseModel):
    number: str


@app.post("/api/call/start")
async def start_call(body: StartBody, request: Request):
    limit(request, "start")
    s = get_settings()
    allowed = norm_number(body.number) in {norm_number(n) for n in s["allow_list"]}
    call = {
        "id": uuid.uuid4().hex[:10],
        "number": body.number.strip(),
        "started_at": time.time(),
        "ended_at": None,
        "status": "ringing_through" if allowed else "screening",
        "allow_listed": allowed,
        "parent_name": s["parent_name"],
        "lang": s.get("greeting_language", lang.DEFAULT),   # Gena's current language
        "caller_lang": None,                                 # detected from the caller's first answer
        "turns": [],
        "steps": list(script.BASE_STEPS),
        "step_index": 0,
        "reasked": False,
        "code_word_status": "not_asked",
        "risk": risk.assess("", family_names(s)),
        "message_audio": {},
    }
    if allowed:
        call["status"] = "ended"
        call["ended_at"] = time.time()
        call["risk"]["verdict"] = "allow"
        call["risk"]["reasons"] = ["Saved contact, rang straight through (never screened)"]
        save_call(call)
        return {"call_id": call["id"], "allow_listed": True, "done": True}
    prompt = await _with_audio(_prompt(call, "name"))
    save_call(call)
    return {"call_id": call["id"], "allow_listed": False, "done": False, "prompt": prompt}


async def _advance(call: dict, transcript: str, meta: dict) -> dict:
    s = get_settings()
    step = call["steps"][call["step_index"]]
    transcript = (transcript or "").strip()

    # Empty / unclear answer: re-ask once, then move on.
    if len(risk.normalize(transcript)) < 2 and not call["reasked"]:
        call["reasked"] = True
        prompt = await _with_audio(_prompt(call, step, reask=True))
        save_call(call)
        return {"transcript": transcript, "done": False, "risk": call["risk"], "prompt": prompt}
    call["reasked"] = False

    # Mirror the caller: detect their language from the first real answer, then Gena
    # asks the remaining questions (and says goodbye) in that language.
    spoke = None
    if transcript:
        spoke = lang.detect(transcript, meta.get("detected_language"))
        if call.get("caller_lang") is None and spoke:
            call["caller_lang"] = spoke
            if spoke in lang.LANGS:
                call["lang"] = spoke

    call["turns"].append({"step": step, "question": call.get("last_question", ""),
                          "transcript": transcript or "(no answer)", "spoke": spoke, **meta})

    if step == "codeword":
        if not transcript:
            call["code_word_status"] = "missing"
        else:
            ok = risk.check_code_word(transcript, [s["code_word"]])
            call["code_word_status"] = "correct" if ok else "wrong"

    r = _evaluate(call, s)
    call["risk"] = r

    # Family claim -> ask once more, even if already red: the optional code word
    # if the family turned it on, otherwise "what's your relation + full name"
    # (the family then verifies by calling back on a number they already have).
    if r["family_claim"] and not ({"codeword", "relation"} & set(call["steps"])):
        rest = call["steps"][call["step_index"] + 1:]
        if s.get("code_word_enabled") and s.get("code_word"):
            call["steps"].insert(call["step_index"] + 1, "codeword")
        elif "org" in rest:   # "which company?" makes no sense for a relative
            call["steps"][call["steps"].index("org", call["step_index"] + 1)] = "relation"
        else:
            call["steps"].insert(call["step_index"] + 1, "relation")

    call["step_index"] += 1
    next_step = call["steps"][call["step_index"]] if call["step_index"] < len(call["steps"]) else None
    finished = (next_step is None
                or (r["verdict"] == risk.RED and next_step not in ("codeword", "relation"))
                or len(call["turns"]) >= MAX_TURNS)

    if finished:
        call["status"] = "ended"
        call["ended_at"] = time.time()
        save_call(call)
        close = "close_" + r["verdict"]
        if r["verdict"] == risk.YELLOW and r.get("verify_by_callback"):
            close = "close_family"
        p = await _with_audio(_prompt(call, close))
        save_call(call)
        return {"transcript": transcript, "done": True, "risk": r, "prompt": p}

    nxt = call["steps"][call["step_index"]]
    p = await _with_audio(_prompt(call, nxt))
    save_call(call)
    return {"transcript": transcript, "done": False, "risk": r, "prompt": p}


@app.post("/api/call/{call_id}/answer")
async def answer_audio(call_id: str, request: Request, audio: UploadFile = File(...)):
    limit(request, "answer")
    call = find_call(call_id)
    if call["status"] != "screening":
        raise HTTPException(409, "call already ended")
    wav = await audio.read()
    if len(wav) > 2_000_000:
        raise HTTPException(413, "clip too long (max ~30 s)")
    try:
        body = await gnani.transcribe(wav, languages="indic-auto")   # Prisma v3 detects the caller's language
    except gnani.GnaniError as e:
        raise gnani_error(e)
    meta = {"source": "prisma", "detected_language": body.get("detected_language_code"),
            "latency_s": body.get("end_to_end_latency"), "audio_bytes": len(wav)}
    return await _advance(call, body.get("transcript", ""), meta)


class TextAnswer(BaseModel):
    text: str


@app.post("/api/call/{call_id}/answer_text")
async def answer_text(call_id: str, body: TextAnswer, request: Request):
    """Typed fallback (testing / no mic). Same pipeline minus STT."""
    limit(request, "answer")
    if len(body.text) > 500:
        raise HTTPException(413, "Please keep answers under 500 characters.")
    call = find_call(call_id)
    if call["status"] != "screening":
        raise HTTPException(409, "call already ended")
    return await _advance(call, body.text, {"source": "typed"})


# ------------------------------------------------------------------ dashboard API

@app.get("/api/calls")
def list_calls():
    return get_calls()


@app.delete("/api/calls")
def clear_calls():
    _save(CALLS_FILE, [])
    return {"ok": True}


@app.get("/api/settings")
def read_settings():
    return get_settings()


class SettingsBody(BaseModel):
    parent_name: str
    parent_language: str
    greeting_language: str = lang.DEFAULT
    code_word_enabled: bool = False
    code_word: str
    family_names: list
    allow_list: list


@app.post("/api/settings")
async def write_settings(body: SettingsBody, request: Request):
    limit(request, "settings")
    d = body.dict()
    # keep a public demo tidy: short values only, known languages only
    d["parent_name"] = d["parent_name"].strip()[:40] or DEFAULT_SETTINGS["parent_name"]
    d["code_word"] = d["code_word"].strip()[:40]
    d["family_names"] = [str(x).strip()[:30] for x in d["family_names"]][:10]
    d["allow_list"] = [str(x).strip()[:60] for x in d["allow_list"]][:10]
    for k in ("parent_language", "greeting_language"):
        if d[k] not in lang.LANGS:
            d[k] = DEFAULT_SETTINGS[k]
    s = get_settings()
    s.update(d)
    _save(SETTINGS_FILE, s)
    lg = s.get("greeting_language", lang.DEFAULT)
    await tts_url(lang.lines(s["parent_name"], lg)["name"][0], lg)  # re-render greeting
    return s


class PlayBody(BaseModel):
    language: Optional[str] = None


@app.post("/api/calls/{call_id}/parent_message")
async def parent_message(call_id: str, body: PlayBody, request: Request):
    limit(request, "relay")
    call = find_call(call_id)
    if call["risk"]["verdict"] != risk.GREEN:
        raise HTTPException(400, "messages are only relayed for low-risk calls")
    family_lang = body.language or get_settings()["parent_language"]
    text = _caller_text(call)
    purpose = " ".join(t["transcript"] for t in call["turns"] if t["step"] in ("purpose", "org"))
    caller_lang = call.get("caller_lang") or call.get("lang", lang.DEFAULT)
    clips = lang.parent_message(risk.benign_intent(text), purpose, family_lang, caller_lang)
    urls = []
    for t, l in clips:
        u = await tts_url(t, l)
        if not u:
            raise HTTPException(502, "Timbre TTS failed")
        urls.append(u)
    return {"clips": [{"text": t, "language": l, "audio_url": u} for (t, l), u in zip(clips, urls)]}


@app.get("/api/languages")
def languages():
    return {code: {"name": en, "native": native} for code, (en, native) in lang.LANGS.items()}


@app.get("/api/health")
def health():
    return {"ok": True, "gnani_key_configured": gnani.has_key(), "usage": gnani.usage(),
            "stt": f"{gnani.STT_URL} ({gnani.STT_MODEL})", "tts": f"{gnani.TTS_URL} ({gnani.TTS_MODEL})"}


# ------------------------------------------------------------------ pages

@app.get("/")
def root():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/caller")
def caller_page():
    return FileResponse(ROOT / "static" / "caller.html")


@app.get("/dashboard")
def dashboard_page():
    return FileResponse(ROOT / "static" / "dashboard.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
