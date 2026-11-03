#!/usr/bin/env python3
# jsfetch: pobiera bundle JS z manifestu (rate-limited 4.5 rps, GET-only, pliki publiczne
# — te same, które pobiera przeglądarka) + próbuje sourcemap (.map). Wynik: out/js/
import json, os, re, sys, time, urllib.request, urllib.error, hashlib
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
JSD = os.path.join(OUT, "js")
os.makedirs(JSD, exist_ok=True)
UA = "nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
CAP = 48

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def main():
    manifest = json.load(open(os.path.join(OUT, "js-manifest.json"), encoding="utf-8"))
    audit = open(os.path.join(OUT, "requests.jsonl"), "a", encoding="utf-8")
    n = 0
    saved = []
    for item in manifest:
        if n >= CAP:
            break
        for suffix in ("", ".map"):
            if n >= CAP:
                break
            host, path = item["host"], item["path"]
            url = f"https://{host}{path}{suffix}"
            if ".map" == suffix and path.endswith(".map"):
                continue
            time.sleep(0.25)
            n += 1
            rec = {"ts": now(), "module": "jsfetch", "url": url}
            try:
                q = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
                r = urllib.request.urlopen(q, timeout=20)
                body = r.read(20_000_000)
                rec.update(status=r.status, len=len(body))
                if r.status == 200 and len(body) > 64:
                    fn = f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}{suffix or '' }.js" if not path.endswith(".js") else f"{host}__{hashlib.sha1((path+suffix).encode()).hexdigest()[:8]}.js"
                    with open(os.path.join(JSD, fn), "wb") as f:
                        f.write(body)
                    saved.append({"file": fn, "url": url, "len": len(body)})
            except Exception as e:
                rec.update(error=f"{type(e).__name__}: {e}")
            audit.write(json.dumps(rec, ensure_ascii=False) + "\n")
            audit.flush()
    json.dump(saved, open(os.path.join(JSD, "saved.json"), "w", encoding="utf-8"), indent=1)
    print(f"jsfetch: {len(saved)} plików zapisano ({n} żądań)", flush=True)

if __name__ == "__main__":
    main()
