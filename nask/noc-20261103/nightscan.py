#!/usr/bin/env python3
# nocny skaner NASK bug bounty (hack.cert.pl, program NASK, edycja 11/2026, 3-30.11)
# ZGODNOŚĆ Z REGULAMINEM (twarde):
#   - TYLKO 12 hostów z §5 (guard: każde żądanie sprawdzane przed wysłaniem)
#   - globalny limiter 4.5 req/s (regulamin: max 5) — pojedynczy wątek
#   - GET-only, bez uwierzytelnienia, bez DoS/obciążenia, bez modyfikacji danych
#   - każde żądanie logowane (audyt: out/requests.jsonl)
# Moduły: sweep(nagłówki/tech) + wafcheck + exposure(16 ścieżek + baseline catch-all,
# reguła "nie-HTML") + nextjs(__NEXT_DATA__, buildId, _next/data, _next/image SSRF-probe)
# + wp(fingerprint wtyczek + readme.txt wersje vs znane CVE z publicznym PoC)
# + robots/sitemap/security.txt + kandydat zDiscovery.
import urllib.request, urllib.error, urllib.parse, json, re, time, hashlib, random, sys, os, gzip, io
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

SCOPE = {  # host -> tier (dokładnie z §5 programu NASK)
    "nask.pl": 1, "dyzurnet.pl": 1, "dns.pl": 1, "oad.nask.pl": 1, "zglos-dezinformacje.nask.pl": 1,
    "bezpiecznymiesiac.pl": 2, "secure.edu.pl": 2, "bezpiecznewybory.pl": 2, "116sos.pl": 2,
    "pllum.org.pl": 2, "science.nask.pl": 2, "dataannotation.pllum.org.pl": 2,
}
RPS = 4.5
MINIV = 1.0 / RPS
TOTAL_CAP = 400
UA_HONEST = "nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

EXPOSURE_PATHS = [
    "/.git/HEAD", "/.env", "/.env.local", "/config.json", "/backup.zip", "/.svn/entries",
    "/server-status", "/actuator/env", "/actuator/health", "/.well-known/security.txt",
    "/api/v1/users", "/api/users", "/api/v1/config", "/graphql", "/swagger.json", "/openapi.json",
]
WP_VULNS = {  # (wersja naprawcza, opis z publicznym PoC) — flaga TYLKO gdy wersja wykryta i < naprawczej
    "wp-file-manager": ("7.9", "CVE-2020-25213 RCE (elfinder ajax), publiczny PoC"),
    "contact-form-7": ("5.3.9", "CVE-2020-35489 unrestricted upload, publiczny PoC"),
    "duplicator": ("1.3.28", "CVE-2020-11738 path traversal (backup download), publiczny PoC"),
    "elementor": ("3.6.2", "CVE-2022-1329 RCE (onboarding), publiczny PoC"),
}

_sent = 0
_last = 0.0
_audit = open(os.path.join(OUT, "requests.jsonl"), "a", encoding="utf-8")

def log_audit(rec):
    _audit.write(json.dumps(rec, ensure_ascii=False) + "\n")
    _audit.flush()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def req(host, path, ua=UA_HONEST, module="?", extra_headers=None):
    """GET https://host/path; zwraca dict wyniku lub błędu; limituje tempo globalnie."""
    global _sent, _last
    if host not in SCOPE:
        log_audit({"ts": now(), "skipped_out_of_scope": host, "path": path})
        return None
    if _sent >= TOTAL_CAP:
        log_audit({"ts": now(), "budget_stop": True, "sent": _sent})
        return None
    wait = _last + MINIV - time.time()
    if wait > 0:
        time.sleep(wait)
    _last = time.time()
    _sent += 1
    url = f"https://{host}{path}"
    t0 = time.time()
    r = {"ts": now(), "module": module, "host": host, "path": path, "url": url}
    try:
        h = {"User-Agent": ua, "Accept-Encoding": "identity", "Accept": "*/*"}
        if extra_headers:
            h.update(extra_headers)
        q = urllib.request.Request(url, headers=h, method="GET")
        try:
            resp = opener.open(q, timeout=15)
            body = resp.read(2_000_000)
            r.update(status=resp.status, hdrs=dict(list(resp.headers.items())[:30]))
        except urllib.error.HTTPError as e:
            body = e.read(2_000_000)
            r.update(status=e.code, hdrs=dict(list(e.headers.items())[:30]))
        ct = r.get("hdrs", {}).get("Content-Type", r.get("hdrs", {}).get("content-type", ""))
        r["ct"] = ct.split(";")[0].strip()
        r["len"] = len(body)
        r["sha"] = hashlib.sha256(norm_body(body, path)).hexdigest()[:16]
        r["body_hex_collapsed_sample"] = norm_body(body, path)[:220].decode("utf-8", "replace")
        if "gzip" in ct:
            pass
        loc = r.get("hdrs", {}).get("Location", r.get("hdrs", {}).get("location", ""))
        if loc:
            r["location"] = loc
        r["body_head"] = body[:400].decode("utf-8", "replace")
    except Exception as e:
        r.update(error=f"{type(e).__name__}: {e}", t=round(time.time() - t0, 2))
        log_audit(r)
        return r
    r["t"] = round(time.time() - t0, 2)
    log_audit(r)
    return r

def norm_body(b, path):
    b = b.replace(path.encode(), b"@P@")
    return re.sub(rb"[0-9a-f]{16,}", b"<HEX>", b)

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def is_html(r):
    return r and (r.get("ct", "") in ("text/html", "") and b"<html" in r.get("body_head", "").lower().encode() or r.get("ct") == "text/html")

def findings_add(lst, sev, host, what, evidence):
    lst.append({"sev": sev, "host": host, "what": what, "evidence": evidence, "ts": now()})
    print(f"[{sev}] {host}: {what}", flush=True)

def main():
    random.seed(20261103)
    F = []  # findings
    home = {}
    print(f"start {now()} cap={TOTAL_CAP} rps<={RPS}", flush=True)

    # ---- 1. sweep + zbieranie HTML głównych stron
    for h in sorted(SCOPE):
        r = req(h, "/", module="sweep")
        if r and not r.get("error"):
            hdrs = {k.lower(): v for k, v in r.get("hdrs", {}).items()}
            tech = {
                "server": hdrs.get("server", ""), "azure": "x-azure-ref" in hdrs,
                "envoy": "x-envoy-upstream-service-time" in hdrs, "nextjs": ("x-nextjs-cache" in hdrs),
                "cloudflare": "cloudflare" in hdrs.get("server", "").lower(),
                "cache": hdrs.get("x-cache", hdrs.get("x-cache-info", "")),
                "powered": hdrs.get("x-powered-by", ""),
                "cookies": [c.split("=")[0] for c in hdrs.get("set-cookie", "").split("\n") if c],
            }
            home[h] = r
            findings_add(F, "INFO", h, f"alive {r['status']} len={r['len']}", json.dumps(tech, ensure_ascii=False))
        else:
            findings_add(F, "INFO", h, "nie odpowiada (HTTPS/443)", json.dumps(r or {}))

    # ---- 2. wafcheck: bezpiecznewybory/secure.edu z UA przeglądarki (1 req każdy)
    for h in ("bezpiecznewybory.pl", "secure.edu.pl"):
        rb = req(h, "/", ua=UA_BROWSER, module="wafcheck")
        if rb and not rb.get("error"):
            findings_add(F, "INFO", h, f"UA-browser status={rb['status']} len={rb['len']}",
                         f"ct={rb.get('ct')} head={rb.get('body_head','')[:150]!r}")

    # ---- 3. exposure: 16 ścieżek × host, baseline catch-all + reguła nie-HTML
    for h in sorted(SCOPE):
        base = req(h, f"/{os.urandom(8).hex()}", module="exposure-baseline")
        if not base or base.get("error"):
            continue
        for p in EXPOSURE_PATHS:
            r = req(h, p, module="exposure")
            if not r or r.get("error"):
                continue
            nonhtml = r.get("ct", "text/html") != "text/html"
            basehtml = base.get("ct", "text/html") == "text/html"
            if nonhtml and r["status"] != base["status"] and r["sha"] != base["sha"]:
                sev = "HIGH" if r["status"] == 200 and not p.startswith("/.well-known/security.txt") else (
                    "INFO" if "security.txt" in p else "MED")
                findings_add(F, sev, h, f"ekspozycja {p}", f"status={r['status']} ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:200]!r}")
            elif r["status"] != base["status"] and basehtml and not nonhtml:
                findings_add(F, "NEARMISS", h, f"status-inny {p}", f"status={r['status']} vs base={base['status']} (HTML — raczej catch-all/router)")

    # ---- 4. nextjs: __NEXT_DATA__, buildId, _next/data, _next/image SSRF-probe
    for h, r0 in home.items():
        if not r0 or r0.get("error"):
            continue
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', r0.get("body_head", "") + ("" if len(r0.get("body_head", "")) < 400 else ""), re.S)
        # pełne ciało potrzebne — pobierz / ponownie tylko gdy główna strona miała nextjs-cache albo next w body
        hint = "nextjs" in json.dumps(r0.get("hdrs", {})).lower() or "__NEXT_DATA__" in r0.get("body_head", "")
        if not hint:
            continue
        full = req(h, "/", module="nextjs-html")  # pełny body w body_head mamy tylko 400B — pobierz i parsuj z requests.jsonl
        html = (full or r0).get("body_head", "")
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', html, re.S)
        if not m:
            continue
        try:
            nd = json.loads(m.group(1))
        except Exception:
            nd = {}
        bid = nd.get("buildId", "")
        page = nd.get("page", "")
        preview = nd.get("preview", None)
        findings_add(F, "INFO", h, "__NEXT_DATA__ obecne", f"buildId={bid!r} page={page!r} preview={preview!r}")
        if bid:
            rd = req(h, f"/_next/data/{bid}/index.json", module="nextjs-data")
            if rd and not rd.get("error") and rd.get("ct") == "application/json" and rd["status"] == 200:
                findings_add(F, "MED", h, f"_next/data odpowiada JSON (buildId={bid})", f"len={rd['len']} head={rd.get('body_head','')[:200]!r}")
        for label, target in (("loopback", "http%3A%2F%2F127.0.0.1%3A3000%2F"), ("imds", "http%3A%2F%2F169.254.169.254%2Flatest%2Fmeta-data%2F")):
            ri = req(h, f"/_next/image?url={target}&w=64&q=10", module="nextjs-image")
            if ri and not ri.get("error") and ri["status"] == 200 and ri.get("ct", "").startswith("image/"):
                findings_add(F, "HIGH", h, f"_next/image czyta WEWNĘTRZNY URL ({label}) → SSRF poz.5.2", f"ct={ri.get('ct')} len={ri['len']}")
        rext = req(h, "/_next/image?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftwitter%2Ftwemoji%2Fmaster%2Fassets%2F72x72%2F1f600.png&w=64&q=10", module="nextjs-image")
        if rext and not rext.get("error") and rext["status"] == 200:
            findings_add(F, "MED", h, "_next/image przyjmuje DOWOLNY zewnętrzny URL (szerokie remotePatterns) — enabler SSRF", f"ct={rext.get('ct')} len={rext['len']}")

    # ---- 5. wordpress: wtyczki z HTML + readme.txt wersje vs CVE z PoC
    for h, r0 in home.items():
        if not r0 or r0.get("error"):
            continue
        html = r0.get("body_head", "")
        slugs = sorted(set(re.findall(r"wp-content/plugins/([a-z0-9_\-]+)/", html)))[:8]
        if not slugs:
            continue
        findings_add(F, "INFO", h, "WordPress wykryty", f"wtyczki z HTML: {slugs}")
        for s in slugs:
            rr = req(h, f"/wp-content/plugins/{s}/readme.txt", module="wp-version")
            if rr and not rr.get("error") and rr["status"] == 200:
                vm = re.search(r"Stable tag:\s*([0-9][0-9.]*)", rr.get("body_head", ""))
                if vm:
                    v = vm.group(1)
                    note = ""
                    if s in WP_VULNS:
                        fixed, desc = WP_VULNS[s]
                        if tuple(map(int, v.split("."))) < tuple(map(int, fixed.split("."))):
                            sev = "HIGH"
                            note = f" <<< WERSJA PODATNA: {desc} (fixed {fixed})"
                    findings_add(F, "INFO" if not note else "HIGH", h, f"wtyczka {s} wersja {v}", (note or "readme.txt publiczny"))

    # ---- 6. robots/sitemap/security.txt + kandydaci ścieżek
    for h in sorted(SCOPE):
        rr = req(h, "/robots.txt", module="misc")
        cand = []
        if rr and not rr.get("error") and rr["status"] == 200 and "text/html" not in rr.get("ct", "text/html"):
            for d in re.findall(r"(?:Disallow|Allow):\s*(/\S*)", rr.get("body_head", "")):
                if d not in ("/", "*"):
                    cand.append(d)
            if cand:
                findings_add(F, "INFO", h, "robots.txt ścieżki", ", ".join(sorted(set(cand))[:20]))
        rs = req(h, "/sitemap.xml", module="misc")
        if rs and not rs.get("error") and rs["status"] == 200 and rs.get("ct", "") in ("text/xml", "application/xml"):
            locs = re.findall(r"<loc>([^<]+)</loc>", rs.get("body_head", ""))
            same = [u for u in locs if h in u]
            findings_add(F, "INFO", h, f"sitemap.xml: {len(locs)} URL-i", "; ".join(same[:8]))
        # 1 kandydat z robots na host (z catch-all weryfikacją)
        strong = [c for c in cand if re.search(r"api|admin|upload|panel|manager|graphql|debug|test|backup", c, re.I)]
        if strong:
            c = strong[0]
            base2 = req(h, f"/{os.urandom(8).hex()}?cb=2", module="misc-baseline")
            rc = req(h, c, module="misc-probe")
            if rc and base2 and not rc.get("error") and not base2.get("error") and rc["sha"] != base2["sha"] and rc["status"] != base2["status"]:
                findings_add(F, "NEARMISS", h, f"kandydat z robots {c}", f"status={rc['status']} ct={rc.get('ct')} len={rc['len']}")

    # ---- raport
    order = {"HIGH": 0, "MED": 1, "NEARMISS": 2, "INFO": 3}
    F.sort(key=lambda x: (order.get(x["sev"], 9), x["host"]))
    rep = ["# Nocny skan NASK — raport automatyczny", "",
           f"bieg: {now()} | żądań: {_sent} | limit: {RPS} req/s (regulamin ≤5) | GET-only, bez auth, 12 hostów z §5", "",
           "| sev | host | co | dowód |", "|---|---|---|---|"]
    for f in F:
        ev = f["evidence"].replace("|", "\\|")[:300]
        rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep) + "\n")
    with open(os.path.join(OUT, "findings.json"), "w", encoding="utf-8") as f:
        json.dump(F, f, ensure_ascii=False, indent=1)
    # manifest JS do dalszego minowania (jsdig) — zbierany tu:
    js_manifest = []
    for h, r0 in home.items():
        if not r0 or r0.get("error"):
            continue
        for src in re.findall(r'(?:src|href)="(/[^"]+\.js)"', r0.get("body_head", ""))[:6]:
            js_manifest.append({"host": h, "path": src})
    with open(os.path.join(OUT, "js-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(js_manifest, f, ensure_ascii=False, indent=1)
    print(f"koniec {now()} żądań={_sent} findingów={len(F)}", flush=True)

if __name__ == "__main__":
    main()
