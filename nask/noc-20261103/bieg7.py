#!/usr/bin/env python3
# bieg 7 — dns.pl: D1/D2 (kontrakty z 20-DELTA: POST /api/who-is-xml/{loc} {name,captcha},
# POST /api/domain-browser/{loc} {domain,recaptcha} — semantyka LOOKUP, zero tworzenia rekordów,
# domena testowa = nask.pl, dane organizacji publiczne) + polowanie na współdzielony cache
# dla odbicia X-Forwarded-Host→<script src> (22-RAPORT §3.1) na kolejnych ścieżkach,
# unikalne markery + unikalne cb w query = zatruwamy co najwyżej własny URL.
# Zgodność: 1 host §5 (dns.pl), limiter 4.5 rps, audyt pełny, POST tylko lookup.
import urllib.request, urllib.error, json, time, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
RPS=4.5; MINIV=1/RPS; CAP=24
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:600],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(path,module,method="GET",body=None,headers=None,slow_timeout=20):
    global _sent,_last
    if _sent>=CAP: return None
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    url=f"https://dns.pl{path}"
    r={"ts":now(),"module":module,"host":"dns.pl","path":path,"method":method,"url":url}
    try:
        h={"User-Agent":UA,"Accept-Encoding":"identity","Accept":"*/*"}
        if headers: h.update(headers)
        data=None
        if body is not None:
            data=json.dumps(body).encode()
            h["Content-Type"]="application/json"
        q=urllib.request.Request(url,data=data,headers=h,method=method)
        try:
            resp=urllib.request.urlopen(q,timeout=slow_timeout); raw=resp.read(1_500_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:25]))
        except urllib.error.HTTPError as e:
            raw=e.read(1_500_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:25]))
        hh={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=hh.get("content-type","").split(";")[0].strip(); r["len"]=len(raw)
        r["cache"]=hh.get("cache-control","")
        r["body_head"]=raw[:400].decode("utf-8","replace")
    except Exception as e:
        r.update(error=f"{type(e).__name__}:{str(e)[:90]}")
        audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

print(f"bieg7 start {now()} cap={CAP}",flush=True)

# ---- D1: POST /api/who-is-xml/pl bez captcha i z pustą (2 żądania, lookup) ----
for label,payload in (("bez-captcha",{"name":"nask.pl"}),("pusta-captcha",{"name":"nask.pl","captcha":""})):
    r=req("/api/who-is-xml/pl",f"b7-D1-{label}",method="POST",body=payload)
    if r and not r.get("error"):
        st=r["status"]
        if st==200 and "xml" in str(r.get("ct","")):
            add("HIGH","dns.pl",f"D1 {label}: who-is-xml 200 XML BEZ walidacji captcha!",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:250]!r}")
        elif st==200:
            add("MED","dns.pl",f"D1 {label}: 200 {r.get('ct')} (sprawdzić treść: dane > publiczny whois?)",f"len={r['len']} head={r.get('body_head','')[:250]!r}")
        else:
            add("INFO","dns.pl",f"D1 {label}: status {st} — captcha egzekwowana / kontrakt inny",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:160]!r}")
# ---- D2: POST /api/domain-browser/pl (1 żądanie) ----
r=req("/api/domain-browser/pl","b7-D2",method="POST",body={"domain":"nask.pl","recaptcha":""})
if r and not r.get("error"):
    st=r["status"]
    if st==200:
        add("MED" if "json" in str(r.get("ct","")) else "INFO","dns.pl",f"D2: domain-browser 200 bez tokenu ({r.get('ct')})",f"len={r['len']} head={r.get('body_head','')[:250]!r}")
    else:
        add("INFO","dns.pl",f"D2: status {st}",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:160]!r}")
# wariant form-encoded gdy JSON odrzucony (415/422) — maks 1 dodatkowa próba na D1:
r415=[x for x in F if "415" in str(x) or "422" in str(x)]
if r415:
    global_ok=True
    w=_last+MINIV-time.time()
    if w>0: time.sleep(w)
    _last=time.time(); _sent+=1
    try:
        q=urllib.request.Request("https://dns.pl/api/who-is-xml/pl",data=b"name=nask.pl",
            headers={"User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded"},method="POST")
        resp=urllib.request.urlopen(q,timeout=20); raw=resp.read(1_500_000)
        add("MED","dns.pl",f"D1-form: {resp.status} {resp.headers.get('content-type','')}",f"len={len(raw)} head={raw[:250]!r}")
        audit.write(json.dumps({"ts":now(),"module":"b7-D1-form","status":resp.status,"len":len(raw)},ensure_ascii=False)+"\n")
    except urllib.error.HTTPError as e:
        add("INFO","dns.pl",f"D1-form: status {e.code}",f"len={len(e.read(1000))}")
        audit.write(json.dumps({"ts":now(),"module":"b7-D1-form","status":e.code},ensure_ascii=False)+"\n")
    audit.flush()

# ---- XFH → shared-cache hunt (markery unikalne; cb w query = klucz tylko nasz) ----
def xfh_probe(path,label):
    cb=os.urandom(4).hex()
    marker=f"naskbb-{cb}.example"
    r1=req(f"{path}{'&' if '?' in path else '?'}cb={cb}",f"b7-xfh-{label}",headers={"X-Forwarded-Host":marker})
    if not r1 or r1.get("error"): return
    if marker in r1.get("body_head",""):
        cc=r1.get("cache","")
        # czyste powtórzenie tego samego URL (bez nagłówka) — czy cache serwuje marker innym?
        r2=req(f"{path}{'&' if '?' in path else '?'}cb={cb}",f"b7-xfh2-{label}")
        clean = r2 and not r2.get("error") and marker not in r2.get("body_head","")
        if not clean and r2 and not r2.get("error"):
            add("HIGH","dns.pl",f"XFH+CACHE: {path} serwuje marker BEZ nagłówka (poisoning realny!)",f"cache={cc!r} status={r2['status']}")
        else:
            add("MED","dns.pl",f"XFH odbicie na {path} (brak cache lub private)",f"cache={cc!r} status={r1['status']} czyste-powtórzenie={'OK' if clean else '?'}")
for path,label in (("/","home"),("/pl","pl"),("/en","en"),("/szukaj","szukaj"),("/robots.txt","robots"),("/deleted_domains.txt","ddl-no-content")):
    xfh_probe(path,label)
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["what"]))
rep=["# Nocny skan NASK — BIEG 7 (dns.pl: D1/D2 kontrakty + XFH cache hunt)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET+lookup-POST, 1 host §5","",
"| sev | co | dowód |","|---|---|---|"]
for f in F:
    ev=str(f["evidence"]).replace("|","\\|")[:400]
    rep.append(f"| {f['sev']} | {f['host']}: {f['what']} | {ev} |")
open(os.path.join(OUT,"report7.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings7.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg7 koniec {now()} żądań={_sent}",flush=True)
