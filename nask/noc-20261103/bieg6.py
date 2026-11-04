#!/usr/bin/env python3
# bieg 6 — mapa chunków JS dyzurnet.pl i dns.pl (robi to, co cały zespół odłożył:
# "miner na dyzurnet.pl + dns.pl (chunki) -> mapy"). GET-only publiczne assety,
# limiter 4.5 rps, guard hostów §5, audyt pełny. Dig offline z kontekstem.
import urllib.request, urllib.error, json, re, time, hashlib, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out"); JSD = os.path.join(OUT, "js6"); HTMLD = os.path.join(OUT, "html")
os.makedirs(JSD, exist_ok=True); os.makedirs(HTMLD, exist_ok=True)
SCOPE = {"dyzurnet.pl":1,"dns.pl":1}
RPS=4.5; MINIV=1/RPS; CAP=30
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:500],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(host,path,module="?",binary=False):
    global _sent,_last
    if host not in SCOPE or _sent>=CAP: return None
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    url=f"https://{host}{path}"
    r={"ts":now(),"module":module,"host":host,"path":path,"url":url}
    try:
        q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Encoding":"identity","Accept":"*/*"},method="GET")
        try:
            resp=urllib.request.urlopen(q,timeout=20); body=resp.read(12_000_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:25]))
        except urllib.error.HTTPError as e:
            body=e.read(12_000_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:25]))
        hh={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=hh.get("content-type","").split(";")[0].strip(); r["len"]=len(body)
        r["body_head"]=body[:300].decode("utf-8","replace")
        if binary and r["status"]==200:
            fn=f"{host}__{hashlib.sha1(path.encode()).hexdigest()[:8]}.js"
            open(os.path.join(JSD,fn),"wb").write(body)
    except Exception as e:
        r.update(error=f"{type(e).__name__}:{str(e)[:90]}")
        audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

print(f"bieg6 start {now()} cap={CAP}",flush=True)
PATTERNS=[
 ("api_path", r'["\'](/api/[A-Za-z0-9/_.\-]{2,80})["\']'),
 ("v_path", r'["\'](/v[0-9]/[A-Za-z0-9/_.\-]{2,80})["\']'),
 ("drupal_route", r'["\']((?:/[a-z0-9_\-]{2,40}){1,3}\?_format=json)["\']'),
 ("wp_rest", r'["\'](?:/wp-json/[A-Za-z0-9/_.\-]{2,70}|/index\.php\?rest_route=[A-Za-z0-9/_.\-&=]{2,70})["\']'),
 ("next_data", r'/_next/data/[A-Za-z0-9_\-]+/[A-Za-z0-9/_.\[\]-]{1,60}'),
 ("abs_url", r'https?://[A-Za-z0-9.\-_]+\.[a-z]{2,12}(?::\d{2,5})?(?:/[A-Za-z0-9/_.\-]{0,60})?'),
 ("internal_url", r'https?://(?:localhost|127\.0\.0\.1|[^/"\'`]*\.internal|[^/"\'`]*\.local|[^/"\'`]*azurewebsites\.net|[^/"\'`]*blob\.core\.windows\.net)[:0-9/]{0,10}[^"\'`\s]{0,50}'),
 ("jwt", r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}'),
 ("google_key", r'AIza[0-9A-Za-z_\-]{35}'),
 ("admin_ref", r'["\']([^"\']*(?:/admin|/panel|/login|/moderator)[^"\']{0,60})["\']'),
 ("upload_ref", r'["\']([^"\']*(?:upload|przeslij|zalacznik|attachment|whois|domain-browser)[^"\']{0,60})["\']'),
 ("apikey_word", r'["\'](?:api[_-]?key|apikey|secret|token)["\']\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{8,60})["\']'),
]
BORE=("w3.org","schema.org","reactjs.org","react.dev","nextjs.org","gnu.org","opensource.org","vercel.com","npmjs.com","yarnpkg","polyfill","mozilla.org","wikipedia","googletagmanager","google-analytics","vuejs.org","momentjs","core-js","babeljs","dayjs","bazinga","centr.org","x.com","linkedin","facebook","twitter")
manifest=[]
for host in SCOPE:
    r=req(host,"/",module="b6-home",binary=True)
    if not r or r.get("error") or r.get("status")!=200: continue
    hp=os.path.join(JSD,f"{host}__{hashlib.sha1(b'/').hexdigest()[:8]}.js")
    if not os.path.exists(hp): continue
    html=open(hp,encoding="utf-8",errors="replace").read()
    srcs=set(re.findall(r'(?:src|href)="(/[^"]+?\.js(?:\?[^"]*)?)"',html)) | set(re.findall(r'["\'](/_next/static/[^"\']+?\.js)["\']',html)) | set(re.findall(r'["\'](/sites/default/[^"\']+?\.js)["\']',html)) | set(re.findall(r'["\'](/static/js/[^"\']+?\.js)["\']',html))
    for s in sorted(srcs)[:10]: manifest.append({"host":host,"path":s})
    add("INFO",host,f"homepage: {len(srcs)} skryptów JS",", ".join(sorted(srcs)[:6]))
json.dump(manifest,open(os.path.join(OUT,"js-manifest-6.json"),"w",encoding="utf-8"),indent=1)

for item in manifest:
    if _sent>=CAP: break
    r=req(item["host"],item["path"],module="b6-js",binary=True)
    if r and not r.get("error") and r["status"]==200:
        add("INFO",item["host"],f"JS pobrany {item['path'][:60]}",f"len={r['len']} ct={r.get('ct')}")

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
            if s not in [h[0] for h in hits]: hits.append((s,ctx))
            if len(hits)>=25: break
        if name=="abs_url": hits=[h for h in hits if not any(b in h[0] for b in BORE)]
        for s,ctx in hits: digest.append({"file":fn,"host":host,"pattern":name,"hit":s,"ctx":ctx[:160]})
json.dump(digest,open(os.path.join(OUT,"jsdig6.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
from collections import Counter
c=Counter((d["host"],d["pattern"]) for d in digest)
print("digest6:",len(digest),dict(c),flush=True)
for (host,pat),n in c.most_common(10):
    add("INFO",host,f"JS dig: {pat} ×{n}","szczegóły: out/jsdig6.json")
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["host"]))
rep=["# Nocny skan NASK — BIEG 6 (mapa chunków JS: dyzurnet.pl + dns.pl)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET-only, 2 hosty §5","",
"Pełny digest: `jsdig6.json`","",
"| sev | host | co | dowód |","|---|---|---|---|"]
for f in F:
    ev=str(f["evidence"]).replace("|","\\|")[:300]
    rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
open(os.path.join(OUT,"report6.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings6.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg6 koniec {now()} żądań={_sent}",flush=True)
