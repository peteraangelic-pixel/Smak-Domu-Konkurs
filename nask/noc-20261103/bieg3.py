#!/usr/bin/env python3
# bieg 3 — noc 03/04.11: minerał JS w runnerze (znaleziska z KONTEKSTEM, komitowane),
# _next/data na buildId (116sos/science), refleksja X-Forwarded-Host (cache-key probe,
# unikalne cb → zero wpływu na innych), /en zglos-dezinformacje, whois dns.pl (mapa formularza).
# Zgodność: 12 hostów §5, limiter 4.5 rps, GET-only, bez auth, audyt pełny.
import urllib.request, urllib.error, json, re, time, hashlib, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out"); JSD = os.path.join(OUT, "js")
os.makedirs(JSD, exist_ok=True)

SCOPE = {"nask.pl":1,"dyzurnet.pl":1,"dns.pl":1,"oad.nask.pl":1,"zglos-dezinformacje.nask.pl":1,
"bezpiecznymiesiac.pl":2,"secure.edu.pl":2,"bezpiecznewybory.pl":2,"116sos.pl":2,
"pllum.org.pl":2,"science.nask.pl":2,"dataannotation.pllum.org.pl":2}
RPS=4.5; MINIV=1/RPS; CAP=150
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:500],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(host,path,module="?",headers=None,save_body=None):
    global _sent,_last
    if host not in SCOPE or _sent>=CAP: return None
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    url=f"https://{host}{path}"
    r={"ts":now(),"module":module,"host":host,"path":path,"url":url}
    try:
        h={"User-Agent":UA,"Accept-Encoding":"identity","Accept":"*/*"}
        if headers: h.update(headers)
        q=urllib.request.Request(url,headers=h,method="GET")
        try:
            resp=urllib.request.urlopen(q,timeout=15); body=resp.read(8_000_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:30]))
        except urllib.error.HTTPError as e:
            body=e.read(8_000_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:30]))
        hh={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=hh.get("content-type","").split(";")[0].strip(); r["len"]=len(body)
        if hh.get("location"): r["location"]=hh["location"]
        r["body_head"]=body[:300].decode("utf-8","replace")
        if save_body and r["status"]==200:
            open(os.path.join(save_body, f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}.html"),"wb").write(body)
    except Exception as e:
        r.update(error=f"{type(e).__name__}: {str(e)[:100]}")
        audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

print(f"bieg3 start {now()} cap={CAP}",flush=True)

# ---- 1. pełne homepage + manifest JS ----
manifest=[]
for host in sorted(SCOPE):
    r=req(host,"/",module="b3-home",save_body=OUT)
    if not r or r.get("error") or r.get("status")!=200: continue
    fn=f"{host}__"+hashlib.sha1(b"/").hexdigest()[:8]+".html"
    p=os.path.join(OUT,fn)
    if not os.path.exists(p): continue
    html=open(p,encoding="utf-8",errors="replace").read()
    srcs=set(re.findall(r'(?:src|href)="(/[^"]+?\.(?:js|mjs))(?:\?[^"]*)?"',html)) | set(re.findall(r'["\'](/_next/static/[^"\']+?\.js)["\']',html))
    for s in sorted(srcs)[:6]: manifest.append({"host":host,"path":s})
json.dump(manifest,open(os.path.join(OUT,"js-manifest-3.json"),"w",encoding="utf-8"),indent=1)

# ---- 2. pobór JS ----
for item in manifest:
    if _sent>=CAP-25: break
    host,path=item["host"],item["path"]
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    url=f"https://{host}{path}"
    rec={"ts":now(),"module":"b3-js","url":url}
    try:
        q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity"})
        resp=urllib.request.urlopen(q,timeout=20); body=resp.read(20_000_000)
        rec.update(status=resp.status,len=len(body))
        if resp.status==200 and len(body)>64:
            open(os.path.join(JSD,f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}.js"),"wb").write(body)
    except Exception as e:
        rec.update(error=f"{type(e).__name__}:{str(e)[:80]}")
    audit.write(json.dumps(rec,ensure_ascii=False)+"\n"); audit.flush()

# ---- 3. jsdig inline z kontekstem ----
PATTERNS=[
 ("api_path", r'["\'](/api/[A-Za-z0-9/_.\-]{2,80})["\']'),
 ("v_path", r'["\'](/v[0-9]/[A-Za-z0-9/_.\-]{2,80})["\']'),
 ("next_data", r'/_next/data/[A-Za-z0-9_\-]+/[A-Za-z0-9/_.\[\]-]{1,60}'),
 ("abs_url", r'https?://[A-Za-z0-9.\-_]+\.[a-z]{2,12}(?::\d{2,5})?(?:/[A-Za-z0-9/_.\-]{0,60})?'),
 ("internal_url", r'https?://(?:localhost|127\.0\.0\.1|[^/"\'`]*\.internal|[^/"\'`]*\.local|[^/"\'`]*azurewebsites\.net|[^/"\'`]*blob\.core\.windows\.net|[^/"\'`]*database\.windows\.net|[^/"\'`]*envoy[^/"\'`]*)[:0-9/]{0,10}[^"\'`\s]{0,50}'),
 ("jwt", r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}'),
 ("aws_key", r'AKIA[0-9A-Z]{16}'),
 ("github_tok", r'gh[pousr]_[A-Za-z0-9]{30,40}'),
 ("google_key", r'AIza[0-9A-Za-z_\-]{35}'),
 ("privkey", r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
 ("next_public", r'NEXT_PUBLIC_[A-Z_]{2,40}\s*[:=]\s*["\']([^"\']{1,120})["\']'),
 ("graphql", r'["\'](?:/graphql|/api/graphql[^"\']*)["\']'),
 ("websocket", r'wss?://[A-Za-z0-9.\-_:]{3,80}[^\s"\'<>]{0,50}'),
 ("email_inst", r'[A-Za-z0-9._%+\-]+@(?:nask\.pl|dns\.pl|cert\.pl)[a-z0-9._%+\-]*'),
 ("bearer", r'[Bb]earer\s+[A-Za-z0-9_\-\.=]{20,80}'),
 ("apikey_word", r'["\'](?:api[_-]?key|apikey|secret|token)["\']\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{8,60})["\']'),
 ("upload_ref", r'["\']([^"\']*(?:upload|przeslij|zalacznik|attachment)[^"\']{0,60})["\']'),
 ("admin_ref", r'["\']([^"\']*(?:/admin|/panel|/moderator|/moderacja)[^"\']{0,60})["\']'),
]
BORE=("w3.org","schema.org","reactjs.org","react.dev","nextjs.org","gnu.org","opensource.org","vercel.com","github.com/facebook","npmjs.com","yarnpkg","polyfill","mozilla.org","wikipedia","google.com/search","youtube.com/embed","googleapis.com/js","googletagmanager","google-analytics","matomo","hotjar")
digest=[]
for fn in sorted(os.listdir(JSD)):
    p=os.path.join(JSD,fn)
    if not os.path.isfile(p) or os.path.getsize(p)<64: continue
    try: data=open(p,encoding="utf-8",errors="replace").read()
    except Exception: continue
    host=fn.split("__")[0]
    for name,pat in PATTERNS:
        hits=[]
        for m in re.finditer(pat,data):
            s=m.group(1) if m.groups() else m.group(0)
            if len(s)>160: s=s[:160]
            ctx=data[max(0,m.start()-50):m.end()+50].replace("\n"," ")
            if s not in [h[0] for h in hits]:
                hits.append((s,ctx))
            if len(hits)>=25: break
        if name=="abs_url":
            hits=[h for h in hits if not any(b in h[0] for b in BORE)]
        for s,ctx in hits:
            digest.append({"file":fn,"host":host,"pattern":name,"hit":s,"ctx":ctx[:160]})
json.dump(digest,open(os.path.join(OUT,"jsdig3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
from collections import Counter
c=Counter((d["host"],d["pattern"]) for d in digest)
print("digest:",len(digest),"wpisów;",dict(c),flush=True)

# ---- 4. _next/data probe (116sos, science) + /en + whois + XFH ----
BID={"116sos.pl":"8CjJwbyxpVqpWnorny23T","science.nask.pl":"Grl_YQ5SCHd1ahmhesPv6"}
for h,b in BID.items():
    r=req(h,f"/_next/data/{b}/index.json",module="b3-nextdata")
    if r and not r.get("error") and r.get("ct")=="application/json":
        add("MED",h,f"_next/data index.json otwarte JSON (buildId {b})",f"len={r['len']} head={r.get('body_head','')[:150]!r}")
r2=req("116sos.pl","/_next/data/8CjJwbyxpVqpWnorny23T/IPZ-PTP.json",module="b3-nextdata")
if r2 and not r2.get("error") and r2.get("ct")=="application/json":
    add("MED","116sos.pl","_next/data strona /IPZ-PTP jako JSON (propsy SSR wycieku)",f"len={r2['len']} head={r2.get('body_head','')[:150]!r}")
req("zglos-dezinformacje.nask.pl","/en",module="b3-en",save_body=OUT)
rw=req("dns.pl","/whois",module="b3-whois",save_body=OUT)
if rw and not rw.get("error"):
    whp=[f for f in os.listdir(OUT) if f.startswith("dns.pl__") and f.endswith(".html")]
    if whp:
        wh=open(os.path.join(OUT,whp[0]),encoding="utf-8",errors="replace").read()
        inputs=re.findall(r'<input[^>]*name="([^"]+)"[^>]*>',wh)[:10]
        actions=re.findall(r'<form[^>]*action="([^"]+)"',wh)[:4]
        add("INFO","dns.pl","whois formularz",f"inputs={inputs} actions={actions}")
# XFH refleksja (cache probe; cb unikalne = tylko nasza własna keszowana kopia)
for h in ("zglos-dezinformacje.nask.pl","oad.nask.pl","bezpiecznymiesiac.pl","pllum.org.pl","dataannotation.pllum.org.pl"):
    cb=os.urandom(5).hex()
    rr=req(h,f"/?npcb={cb}",module="b3-xfh",headers={"X-Forwarded-Host":f"naskbb-{cb}.example"})
    if rr and not rr.get("error") and f"naskbb-{cb}.example" in rr.get("body_head",""):
        cc=(rr.get("hdrs") or {}).get("Cache-Control") or (rr.get("hdrs") or {}).get("cache-control") or ""
        add("MED",h,"X-Forwarded-Host REFLEKTUJE się w treści (kandydat cache poisoning poz.18)",f"cache-control={cc!r} status={rr['status']}")

# ---- 5. probe API z digestu dataannotation (na bazie znalezionych ścieżek) ----
da_paths=sorted({d["hit"] for d in digest if d["host"]=="dataannotation.pllum.org.pl" and d["pattern"] in ("api_path","v_path")})[:6]
for pth in da_paths:
    r=req("dataannotation.pllum.org.pl",pth,module="b3-da-api")
    if r and not r.get("error") and r.get("status") not in (401,403,404) and r.get("ct")!="text/html":
        add("MED","dataannotation.pllum.org.pl",f"API {pth} status {r['status']}",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:150]!r}")

# ---- raport ----
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["host"]))
rep=["# Nocny skan NASK — BIEG 3 (JS dig z kontekstem + probe celowane)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET-only, bez auth, 12 hostów §5","",
"Uwaga: pełny digest JS → `jsdig3.json` (konteksty ±50 znaków).","",
"| sev | host | co | dowód |","|---|---|---|---|"]
for f in F:
    ev=str(f["evidence"]).replace("|","\\|")[:300]
    rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
open(os.path.join(OUT,"report3.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings3.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg3 koniec {now()} żądań={_sent} findingów={len(F)}",flush=True)
