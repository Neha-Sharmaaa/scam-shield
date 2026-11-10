"""Build the static site for Vercel into .deploy/scam-shield/ (gitignored).

Vercel serves the pages and media; every /api/* request is proxied to the Render backend,
so the browser only ever talks to one origin and the Gnani key stays on Render.

Usage: .venv/bin/python scripts/build_vercel.py https://<your-render-service>.onrender.com
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".deploy" / "scam-shield"
SKIP = {"record.html", "linkedin.html"}                       # internal video-recording stages
SKIP_MEDIA = {"scam-shield-linkedin.mp4", "scam-shield-linkedin.jpg", "scam-shield-demo.mp4", "scam-shield-demo.jpg"}


def main(api: str):
    api = api.rstrip("/")
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "static").mkdir(parents=True)
    for f in (ROOT / "static").rglob("*"):
        rel = f.relative_to(ROOT / "static")
        if f.is_dir() or rel.name in SKIP or (rel.parts[0] == "media" and rel.name in SKIP_MEDIA):
            continue
        dst = OUT / "static" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    (OUT / "vercel.json").write_text(json.dumps({
        "cleanUrls": False,
        "rewrites": [
            {"source": "/api/:path*", "destination": f"{api}/api/:path*"},
            {"source": "/", "destination": "/static/index.html"},
            {"source": "/caller", "destination": "/static/caller.html"},
            {"source": "/dashboard", "destination": "/static/dashboard.html"},
        ],
        "headers": [{"source": "/static/media/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400"}]}],
    }, indent=2))
    print(f"built {OUT} -> API {api}")


if __name__ == "__main__":
    main(sys.argv[1])
