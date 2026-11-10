"""Deploy the static site to Vercel production via the REST API (no CLI login needed).

Usage:
  .venv/bin/python scripts/build_vercel.py https://scam-shield-api-davx.onrender.com
  .venv/bin/python scripts/deploy_vercel.py
Reads VERCEL_TOKEN from .env (needs deploy scope: your team or Full Account).
"""
import hashlib
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / ".deploy" / "scam-shield"


def main():
    tok = (dotenv_values(ROOT / ".env").get("VERCEL_TOKEN") or "").strip().strip('"').strip("'")
    if not tok:
        sys.exit("VERCEL_TOKEN missing in .env")
    if not (SITE / "vercel.json").exists():
        sys.exit("run scripts/build_vercel.py first")
    with httpx.Client(base_url="https://api.vercel.com", headers={"Authorization": f"Bearer {tok}"}, timeout=180) as c:
        user = c.get("/v2/user").json().get("user", {})
        team = {"teamId": user["defaultTeamId"]} if user.get("defaultTeamId") else {}
        files = []
        for f in sorted(p for p in SITE.rglob("*") if p.is_file()):
            data = f.read_bytes()
            sha = hashlib.sha1(data).hexdigest()
            r = c.post("/v2/files", params=team, content=data,
                       headers={"x-vercel-digest": sha, "Content-Type": "application/octet-stream"})
            r.raise_for_status()
            files.append({"file": str(f.relative_to(SITE)), "sha": sha, "size": len(data)})
        r = c.post("/v13/deployments", params={**team, "skipAutoDetectionConfirmation": "1"}, json={
            "name": "scam-shield", "files": files, "target": "production",
            "projectSettings": {"framework": None, "buildCommand": None, "installCommand": None, "outputDirectory": None}})
        r.raise_for_status()
        did = r.json()["id"]
        for _ in range(60):
            st = c.get(f"/v13/deployments/{did}", params=team).json()
            if st.get("readyState") in ("READY", "ERROR", "CANCELED"):
                break
            time.sleep(5)
        print(st.get("readyState"), st.get("alias"))


if __name__ == "__main__":
    main()
