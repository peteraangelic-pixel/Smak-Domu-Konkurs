#!/usr/bin/env python3
# jsdig: offline minerał bundle'ów JS (bez limitów — analiza LOKALNA pobranych plików).
# Szuka: endpointów API, URL-i wewnętrznych, sekretów (JWT/AWS/GitHub/Google/slack),
# NEXT_PUBLIC_ wartosci, sourcemap, graphql, websocket, buildId. Wynik: out/jsfindings.{json,md}
import os, re, sys, json, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
JSD = os.path.join(ROOT, "out", "js")

PATTERNS = [
    ("api_path",      re.compile(r'["\'](/api/[A-Za-z0-9/_.\-]{2,80})["\']')),
    ("v_path",        re.compile(r'["\'](/v[0-9]/[A-Za-z0-9/_.\-]{2,80})["\']')),
    ("abs_url",       re.compile(r'https?://[A-Za-z0-9.\-_]+\.[a-z]{2,12}(?::\d{2,5})?(?:/[A-Za-z0-9/_.\-]{0,80})?')),
    ("internal_url",  re.compile(r'https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|[^/"\']*\.internal|[^/"\']*\.local|[^/"\']*azurewebsites\.net|[^/"\']*blob\.core\.windows\.net|[^/"\']*database\.windows\.net|[^/"\']*redis[^/"\'"]*|[^/"\']*queue[^/"\'"]*)(?::\d{2,5})?[^"\'\s]{0,60}', re.I)),
    ("jwt",           re.compile(r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}')),
    ("aws_key",       re.compile(r'AKIA[0-9A-Z]{16}')),
    ("github_tok",    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,40}')),
    ("google_key",    re.compile(r'AIza[0-9A-Za-z_\-]{35}')),
    ("slack_tok",     re.compile(r'xox[baprs]-[A-Za-z0-9\-]{10,}')),
    ("privkey",       re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ("next_public",   re.compile(r'NEXT_PUBLIC_[A-Z_]{2,40}\s*[:=]\s*["\']([^"\']{1,120})["\']')),
    ("sourcemap_ref", re.compile(r'//#\s*sourceMappingURL=([^\s]+\.map)')),
    ("graphql",       re.compile(r'["\'](?:/graphql|/api/graphql[^"\']*)["\']')),
    ("websocket",     re.compile(r'wss?://[A-Za-z0-9.\-_:]{3,80}[^\s"\'<>]{0,60}')),
    ("buildid",       re.compile(r'["\']buildId["\']\s*:\s*["\']([^"\']{1,60})["\']')),
    ("email",         re.compile(r'[A-Za-z0-9._%+\-]+@(?:nask\.pl|dns\.pl|cert\.pl|nask\.gov\.pl)[^A-Za-z0-9._%+\-]')),
    ("bearer_hdr",    re.compile(r'[Bb]earer\s+[A-Za-z0-9_\-\.=]{20,80}')),
    ("apikey_word",   re.compile(r'["\'](?:api[_-]?key|apikey|secret|token|password)["\']\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{8,60})["\']', re.I)),
]
CAP_PER_PAT = 40

def main():
    files = []
    for fn in sorted(os.listdir(JSD)):
        p = os.path.join(JSD, fn)
        if os.path.isfile(p) and os.path.getsize(p) > 64:
            files.append(p)
    out = []
    for p in files:
        try:
            data = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for name, rx in PATTERNS:
            hits = []
            for m in rx.finditer(data):
                s = (m.group(1) if m.groups() else m.group(0))
                if len(s) > 200:
                    s = s[:200]
                if s not in hits:
                    hits.append(s)
                if len(hits) >= CAP_PER_PAT:
                    break
            if hits:
                # filtr szumu dla abs_url: tylko nie-banalne
                if name == "abs_url":
                    boring = ("w3.org", "schema.org", "reactjs.org", "react.dev", "nextjs.org", "gnu.org", "opensource.org", "vercel.com", "github.com/facebook")
                    hits = [h for h in hits if not any(b in h for b in boring)]
                if hits:
                    out.append({"file": os.path.basename(p), "pattern": name, "hits": hits})
    json.dump(out, open(os.path.join(ROOT, "out", "jsfindings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    md = ["# jsdig — znaleziska w bundle'ach JS", ""]
    cur = None
    for o in out:
        if o["file"] != cur:
            md.append(f"\n## {o['file']}")
            cur = o["file"]
        md.append(f"- **{o['pattern']}**: " + "; ".join(map(str, o["hits"][:12])))
    open(os.path.join(ROOT, "out", "jsfindings.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    n_int = sum(1 for o in out if o["pattern"] in ("internal_url", "jwt", "aws_key", "github_tok", "google_key", "slack_tok", "privkey", "bearer_hdr", "apikey_word"))
    print(f"jsdig: {len(files)} plików, {len(out)} klas znalezisk, {n_int} klas wrażliwych", flush=True)

if __name__ == "__main__":
    main()
