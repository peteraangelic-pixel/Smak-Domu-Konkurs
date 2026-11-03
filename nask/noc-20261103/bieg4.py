#!/usr/bin/env python3
# bieg 4 — noc 03/04.11: probe odkrytych tras z digestu JS.
# dns.pl: /api/domain-browser/, /api/who-is-xml/, /api/stats/, /api/zone-stats, /api/registrars-list/,
#         /api/funny-name/, /api/count-deleted-domains, /api/registrars-services (publiczne dane rejestru)
# science.nask.pl: /api/downloadFile (kontrakt!), /api/search?q=test, /api/contact
# dataannotation: /admin/, /api/v1/
# dyzurnet: /api (po 308)
# zglos-dezinformacje: dogrywanie chunków JS z flight-data i dogłębne minowanie
# Zgodność: 12 hostów §5, limiter 4.5 rps, GET-only, bez auth, audyt pełny, zero zapisów.
import urllib.request, urllib.error, json, re, time, hashlib, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
SCOPE = {"nask.pl":1,"dyzurnet.pl":1,"dns.pl":1,"oad.nask.pl":1,"zglos-dezinformacje.nask.pl":1,
"bezpiecznymiesiac.pl":2,"secure.edu.pl":2,"bezpiecznewybory.pl":2,"116sos.pl":2,
"pllum.org.pl":2,"science.nask.pl":2,"dataannotation.pllum.org.pl":2}
RPS=4.5; MINIV=1/RPS; CAP=80
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:500],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(host,path,module="?",headers=None):
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
            resp=urllib.request.urlopen(q,timeout=15); body=resp.read(4_000_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:30]))
        except urllib.error.HTTPError as e:
            body=e.read(4_000_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:30]))
        hh={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=hh.get("content-type","").split(";")[0].strip(); r["len"]=len(body)
        if hh.get("location"): r["location"]=hh["location"]
        r["body_head"]=body[:600].decode("utf-8","replace")
    except Exception as e:
        r.update(error=f"{type(e).__name__}:{str(e)[:100]}")
        audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

print(f"bieg4 start {now()} cap={CAP}",flush=True)

# ---- dns.pl API ----
for p in ("/api/domain-browser/","/api/who-is-xml/","/api/stats/","/api/zone-stats","/api/registrars-list/","/api/funny-name/","/api/count-deleted-domains","/api/registrars-services"):
    r=req("dns.pl",p,module="b4-dns")
    if not r or r.get("error"): continue
    ct=r.get("ct","")
    if r["status"]==200 and ct not in ("text/html",""):
        add("MED" if "who" in p or "browser" in p else "INFO","dns.pl",f"API {p} otwarte ({ct})",f"len={r['len']} head={r.get('body_head','')[:250]!r}")
    elif r["status"]==200 and ct=="text/html":
        add("INFO","dns.pl",f"API {p} → HTML (SPA-catch-all)",f"len={r['len']}")
    elif r["status"] in (401,403):
        add("INFO","dns.pl",f"API {p} chronione",f"status={r['status']}")
    elif r["status"]>=500:
        add("NEARMISS","dns.pl",f"API {p} → {r['status']} (błąd serwera na GET)",f"ct={ct} head={r.get('body_head','')[:150]!r}")

# ---- science.nask.pl API ----
for p in ("/api/downloadFile","/api/search?q=test","/api/contact"):
    r=req("science.nask.pl",p,module="b4-science")
    if not r or r.get("error"): continue
    if r["status"]==200 and r.get("ct") not in ("text/html",""):
        add("MED","science.nask.pl",f"API {p} odpowiada nie-HTML",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:200]!r}")
    elif r["status"] in (400,405,422,500):
        add("INFO","science.nask.pl",f"API {p} kontrakt",f"status={r['status']} head={r.get('body_head','')[:200]!r}")
    elif r["status"]>=500:
        add("NEARMISS","science.nask.pl",f"API {p} → {r['status']}",f"head={r.get('body_head','')[:150]!r}")

# ---- dataannotation + dyzurnet ----
for h,p in (("dataannotation.pllum.org.pl","/admin/"),("dataannotation.pllum.org.pl","/api/v1/"),("dyzurnet.pl","/api")):
    r=req(h,p,module="b4-app")
    if not r or r.get("error"): continue
    if r["status"]==200 and r.get("ct")=="application/json":
        add("MED",h,f"{p} JSON bez auth",f"len={r['len']} head={r.get('body_head','')[:250]!r}")
    else:
        add("INFO",h,f"{p} status {r['status']}",f"ct={r.get('ct')} len={r['len']} loc={r.get('location','')} head={r.get('body_head','')[:120]!r}")

# ---- zglos-dezinformacje: więcej chunków z zapisanego HTML home ----
html=""
for f in os.listdir(OUT):
    if f.startswith("zglos-dezinformacje.nask.pl__") and f.endswith(".html"):
        html=open(os.path.join(OUT,f),encoding="utf-8",errors="replace").read(); break
chunks=sorted(set(re.findall(r'/_next/static/chunks/[A-Za-z0-9/_.\-]+\.js',html)))
extra=[c for c in chunks if "app/" in c or "page" in c or "layout" in c][:4] or chunks[6:10][:4]
n=0
for c in extra:
    if _sent>=CAP or n>=4: break
    r=req("zglos-dezinformacje.nask.pl",c,module="b4-zglos-js")
    n+=1
    if r and not r.get("error") and r["status"]==200 and r.get("len",0)>500:
        body=r.get("body_head","")
        apis=sorted(set(re.findall(r'/api/[A-Za-z0-9/_.\-]{2,60}',body)))[:10]
        forms=sorted(set(re.findall(r'["\'](/[A-Za-z0-9/_\-]{2,50})["\']\s*[,;]',body)))[:0]
        if apis:
            add("INFO","zglos-dezinformacje.nask.pl",f"API w chunku {c[-40:]}",", ".join(apis))

# ---- raport ----
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["host"]))
rep=["# Nocny skan NASK — BIEG 4 (probe odkrytych tras API)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET-only, bez auth, 12 hostów §5","",
"| sev | host | co | dowód |","|---|---|---|---|"]
for f in F:
    ev=str(f["evidence"]).replace("|","\\|")[:300]
    rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
open(os.path.join(OUT,"report4.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings4.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg4 koniec {now()} żądań={_sent} findingów={len(F)}",flush=True)
