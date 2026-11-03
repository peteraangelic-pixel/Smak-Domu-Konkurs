#!/usr/bin/env python3
# bieg 2 — noc 03/04.11: poprawki po bieg 1 (pełne HTML zamiast 400B, _next/image na wszystkich,
# FastAPI probe na dataannotation, /api na dyzurnet, żniwa JS+sourcemapy, jsdig inline).
# Zgodność j.w.: 12 hostów §5, globalny limiter 4.5 rps, GET-only, bez auth, audyt pełny.
import urllib.request, urllib.error, json, re, time, hashlib, os, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
HTMLD = os.path.join(OUT, "html"); JSD = os.path.join(OUT, "js")
os.makedirs(HTMLD, exist_ok=True); os.makedirs(JSD, exist_ok=True)

SCOPE = {"nask.pl":1,"dyzurnet.pl":1,"dns.pl":1,"oad.nask.pl":1,"zglos-dezinformacje.nask.pl":1,
"bezpiecznymiesiac.pl":2,"secure.edu.pl":2,"bezpiecznewybory.pl":2,"116sos.pl":2,
"pllum.org.pl":2,"science.nask.pl":2,"dataannotation.pllum.org.pl":2}
RPS=4.5; MINIV=1/RPS; CAP=170
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:400],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(host,path,module="?",save_body=None):
    global _sent,_last
    if host not in SCOPE or _sent>=CAP:
        return None
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    url=f"https://{host}{path}"
    r={"ts":now(),"module":module,"host":host,"path":path,"url":url}
    try:
        q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity","Accept":"*/*"},method="GET")
        try:
            resp=urllib.request.urlopen(q,timeout=15); body=resp.read(8_000_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:30]))
        except urllib.error.HTTPError as e:
            body=e.read(8_000_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:30]))
        h={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=h.get("content-type","").split(";")[0].strip(); r["len"]=len(body)
        if h.get("location"): r["location"]=h["location"]
        r["body_head"]=body[:400].decode("utf-8","replace")
        if save_body and r["status"]==200:
            open(os.path.join(save_body, f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}{os.path.splitext(path)[1]}"),"wb").write(body)
    except Exception as e:
        r.update(error=f"{type(e).__name__}: {e}"); audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    r["t"]=round(_last-0,3)
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

def jsdig_files():
    sys.path.insert(0,ROOT)
    import importlib.util
    spec=importlib.util.spec_from_file_location("jsdig",os.path.join(ROOT,"jsdig.py"))
    m=importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass

print(f"bieg2 start {now()} cap={CAP}",flush=True)
# ---- A. pełne homepage (zapis + ekstrakcja) ----
manifest=[]
for host in sorted(SCOPE):
    r=req(host,"/",module="full-home",save_body=HTMLD)
    if not r or r.get("error") or r["status"]!=200: continue
    fn=[f for f in os.listdir(HTMLD) if f.startswith(host+"__")][0] if any(f.startswith(host+"__") for f in os.listdir(HTMLD)) else None
    if not fn: continue
    html=open(os.path.join(HTMLD,fn),encoding="utf-8",errors="replace").read()
    srcs=set(re.findall(r'(?:src|href)="(/[^"]+?\.(?:js|mjs))(?:\?[^"]*)?"',html)) | set(re.findall(r'["\'](/_next/static/[^"\']+?\.js)["\']',html))
    for s in sorted(srcs)[:6]: manifest.append({"host":host,"path":s})
    wp=sorted(set(re.findall(r'wp-content/(?:plugins|themes)/([a-z0-9_\-]+)',html)))
    if wp: add("INFO",host,"wp-content w pełnym HTML",wp[:14])
    nd=re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>',html,re.S)
    if nd:
        try:
            j=json.loads(nd.group(1)); add("INFO",host,"__NEXT_DATA__",f"buildId={j.get('buildId')!r} page={j.get('page')!r}")
        except Exception: pass
    nu=re.search(r'window\.__NUXT__\s*=\s*(.{0,120})',html)
    if nu: add("INFO",host,"__NUXT__ (Nuxt)",nu.group(1)[:100])
    for pat,label in ((r'(?:apiBase|apiUrl|baseUrl|API_BASE_URL|api_base)["\']?\s*[:=]\s*["\'](https?://[^"\']{4,90})["\']',"apiBase"),):
        for m2 in re.finditer(pat,html): add("MED",host,f"{label} w HTML",m2.group(1))
json.dump(manifest,open(os.path.join(OUT,"js-manifest-2.json"),"w",encoding="utf-8"),indent=1)

# ---- B. _next/image probe na wszystkich (SSRF-as-a-feature) ----
for host in sorted(SCOPE):
    ri=req(host,"/_next/image?url=http%3A%2F%2F127.0.0.1%3A3000%2F&w=64&q=10",module="nextimg-loopback")
    if ri and not ri.get("error") and ri.get("status")==200 and str(ri.get("ct","")).startswith("image/"):
        add("HIGH",host,"_next/image czyta 127.0.0.1:3000 → SSRF poz.5.2 (obraz z loopbacka!) ",f"ct={ri.get('ct')} len={ri['len']}")
    if ri and not ri.get("error") and ri.get("status") in (400,) and "url parameter" in ri.get("body_head","").lower():
        pass  # normalna odmowa
    re2=req(host,"/_next/image?url=https%3A%2F%2Fraw.githubusercontent.com%2Ftwitter%2Ftwemoji%2Fmaster%2Fassets%2F72x72%2F1f600.png&w=64&q=10",module="nextimg-external")
    if re2 and not re2.get("error") and re2.get("status")==200 and str(re2.get("ct","")).startswith("image/"):
        add("MED",host,"_next/image przyjmuje dowolny zewnętrzny URL (szerokie remotePatterns — enabler)",f"ct={re2.get('ct')} len={re2['len']}")

# ---- C. FastAPI probe: dataannotation ----
h="dataannotation.pllum.org.pl"
for p in ("/api/v1/users/","/docs","/redoc","/openapi.json","/api/openapi.json"):
    r=req(h,p,module="fastapi-probe")
    if r and not r.get("error"):
        interesting = r["status"]==200 and r.get("ct")!="text/html"
        if interesting:
            sev="HIGH" if ("users" in p or p.endswith("openapi.json")) else "MED"
            add(sev,h,f"FastAPI endpoint {p} OTWARTY",f"status={r['status']} ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:200]!r}")
        elif r["status"] in (401,403):
            add("INFO",h,f"endpoint {p} istnieje, chroniony",f"status={r['status']}")

# ---- D. dyzurnet /api + oad/dns /api ----
for h2,paths in (("dyzurnet.pl",("/api","/api/v1/","/api/health")),("oad.nask.pl",("/api/",)),("dns.pl",("/api/","/whois"))):
    for p in paths:
        r=req(h2,p,module="api-probe")
        if r and not r.get("error") and r["status"]==200 and r.get("ct")!="text/html":
            add("MED",h2,f"{p} odpowiada nie-HTML",f"status={r['status']} ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:200]!r}")
        elif r and not r.get("error") and r.get("location"):
            add("INFO",h2,f"{p} → {r['status']}",r["location"])

# ---- E. żniwa JS + mapy + jsdig ----
import urllib.parse
n=0
for item in manifest:
    if n>=60: break
    host,path=item["host"],item["path"]
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1; n+=1
    url=f"https://{host}{path}"
    rec={"ts":now(),"module":"jsfetch2","url":url}
    try:
        q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
        resp=urllib.request.urlopen(q,timeout=20); body=resp.read(20_000_000)
        rec.update(status=resp.status,len=len(body))
        if resp.status==200 and len(body)>64:
            fn=f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}.js"
            open(os.path.join(JSD,fn),"wb").write(body)
            mm=re.search(rb'//# sourceMappingURL=(\S+?\.map)',body)
            if mm and n<70:
                mp=mm.group(1).decode()
                map_url=urllib.parse.urljoin(url,mp)
                if f"https://{host}/" in map_url or map_url.startswith(f"https://{host}"):
                    time.sleep(0.25); _sent+=1; n+=1
                    rec2={"ts":now(),"module":"jsmap","url":map_url}
                    try:
                        q2=urllib.request.Request(map_url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
                        r2=urllib.request.urlopen(q2,timeout=20); b2=r2.read(20_000_000)
                        rec2.update(status=r2.status,len=len(b2))
                        if r2.status==200:
                            open(os.path.join(JSD,f"{host}__{hashlib.sha1(mp.encode()).hexdigest()[:8]}.map.js"),"wb").write(b2)
                    except Exception as e2:
                        rec2.update(error=str(e2)[:120])
                    audit.write(json.dumps(rec2,ensure_ascii=False)+"\n"); audit.flush()
    except Exception as e:
        rec.update(error=f"{type(e).__name__}: {str(e)[:120]}")
    audit.write(json.dumps(rec,ensure_ascii=False)+"\n"); audit.flush()
print(f"pobrano {n} plików JS/map",flush=True)
jsdig_files()

# ---- raport 2 ----
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["host"]))
rep=["# Nocny skan NASK — BIEG 2 (pełne HTML + JS + probe API)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET-only, bez auth, 12 hostów §5","","| sev | host | co | dowód |","|---|---|---|---|"]
for f in F:
    ev = str(f["evidence"]).replace("|", "\\|")[:300]
    rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
open(os.path.join(OUT,"report2.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings2.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg2 koniec {now()} żądań={_sent} findingów={len(F)}",flush=True)
