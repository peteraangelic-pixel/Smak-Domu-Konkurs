#!/usr/bin/env python3
# bieg 5 — domknięcie nocy: kontrakty /api/downloadFile (science) i /api/domain-browser+
# /api/who-is-xml (dns.pl, z parametrem), 3 płytkie proby /api/search (refleksja, read-only).
# Zgodność: 12 hostów §5, limiter 4.5 rps, GET-only, bez auth, zero zapisów, zero DoS.
import urllib.request, urllib.error, json, time, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
SCOPE = {"nask.pl":1,"dyzurnet.pl":1,"dns.pl":1,"oad.nask.pl":1,"zglos-dezinformacje.nask.pl":1,
"bezpiecznymiesiac.pl":2,"secure.edu.pl":2,"bezpiecznewybory.pl":2,"116sos.pl":2,
"pllum.org.pl":2,"science.nask.pl":2,"dataannotation.pllum.org.pl":2}
RPS=4.5; MINIV=1/RPS; CAP=25
UA="nask-bb-recon/1.0 (hack.cert.pl NASK edition research; researcher via platform)"
_sent=0; _last=0.0
audit=open(os.path.join(OUT,"requests.jsonl"),"a",encoding="utf-8")
F=[]
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def add(sev,host,what,ev):
    F.append({"sev":sev,"host":host,"what":what,"evidence":str(ev)[:600],"ts":now()})
    print(f"[{sev}] {host}: {what}",flush=True)
def req(host,path,module,timeout=25):
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
            resp=urllib.request.urlopen(q,timeout=timeout); body=resp.read(2_000_000)
            r.update(status=resp.status,hdrs=dict(list(resp.headers.items())[:25]))
        except urllib.error.HTTPError as e:
            body=e.read(2_000_000); r.update(status=e.code,hdrs=dict(list(e.headers.items())[:25]))
        hh={k.lower():v for k,v in r.get("hdrs",{}).items()}
        r["ct"]=hh.get("content-type","").split(";")[0].strip(); r["len"]=len(body)
        r["body_head"]=body[:400].decode("utf-8","replace")
        if "content-disposition" in hh: r["disposition"]=hh["content-disposition"]
    except Exception as e:
        r.update(error=f"{type(e).__name__}:{str(e)[:90]} t>{timeout}s")
        audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush(); return r
    audit.write(json.dumps(r,ensure_ascii=False)+"\n"); audit.flush()
    return r

print(f"bieg5 start {now()}",flush=True)
for p in ("/api/domain-browser/nask.pl","/api/who-is-xml/nask.pl","/api/who-is-xml?domain=nask.pl","/api/domain-browser?domain=nask.pl"):
    r=req("dns.pl",p,"b5-dns")
    if r and not r.get("error"):
        if r["status"]==200 and r.get("ct") not in ("text/html",""):
            add("MED","dns.pl",f"{p} otwarte JSON/XML",f"ct={r.get('ct')} len={r['len']} disp={r.get('disposition','')} head={r.get('body_head','')[:250]!r}")
        else:
            add("INFO","dns.pl",f"{p} status {r['status']}",f"ct={r.get('ct')} len={r['len']} head={r.get('body_head','')[:120]!r}")
    elif r:
        add("INFO","dns.pl",f"{p} timeout>{25}s",r.get("error",""))
for p in ("/api/downloadFile?file=README.txt","/api/downloadFile?name=test.txt"):
    r=req("science.nask.pl",p,"b5-science")
    if r and not r.get("error"):
        add("INFO" if r["status"]>=400 else "MED","science.nask.pl",f"{p} status {r['status']}",f"ct={r.get('ct')} len={r['len']} disp={r.get('disposition','')} head={r.get('body_head','')[:200]!r}")
    elif r:
        add("INFO","science.nask.pl",f"{p} zwisa >25s (dlugotrwala operacja?)",r.get("error",""))
for q in ("abc%27","%3Cb%3Exss%3C%2Fb%3E","%7B%7B7%2A7%7D%7D"):
    r=req("science.nask.pl",f"/api/search?q={q}","b5-science-search")
    if r and not r.get("error"):
        reflected = ("xss" in r.get("body_head","").lower()) or ("49" in r.get("body_head","")) or ("%27" in r.get("body_head","")) or ("'" in r.get("body_head","") and "error" not in r.get("body_head","").lower())
        add("NEARMISS" if reflected and r["status"]==200 else "INFO","science.nask.pl",f"/api/search q={q[:20]} status {r['status']}",f"refleksja={reflected} head={r.get('body_head','')[:220]!r}")
order={"HIGH":0,"MED":1,"NEARMISS":2,"INFO":3}
F.sort(key=lambda x:(order.get(x["sev"],9),x["host"]))
rep=["# Nocny skan NASK — BIEG 5 (kontrakty API: downloadFile, domain-browser, search)","",
f"bieg: {now()} | żądań: {_sent} | limit 4.5 rps | GET-only, read-only","","| sev | host | co | dowód |","|---|---|---|---|"]
for f in F:
    ev=str(f["evidence"]).replace("|","\\|")[:400]
    rep.append(f"| {f['sev']} | {f['host']} | {f['what']} | {ev} |")
open(os.path.join(OUT,"report5.md"),"w",encoding="utf-8").write("\n".join(rep)+"\n")
json.dump(F,open(os.path.join(OUT,"findings5.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"bieg5 koniec {now()} żądań={_sent}",flush=True)
