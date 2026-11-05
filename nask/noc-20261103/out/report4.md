# Nocny skan NASK — BIEG 4 (probe odkrytych tras API)

bieg: 2026-11-05T11:16:34+00:00 | żądań: 16 | limit 4.5 rps | GET-only, bez auth, 12 hostów §5

| sev | host | co | dowód |
|---|---|---|---|
| INFO | dataannotation.pllum.org.pl | /admin/ status 200 | ct=text/html len=713 loc= head='<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <meta name="viewport" content="width=device-w' |
| INFO | dataannotation.pllum.org.pl | /api/v1/ status 404 | ct=application/json len=22 loc= head='{"detail":"Not Found"}' |
| INFO | dns.pl | API /api/zone-stats otwarte (application/json) | len=11761 head='{"errors":{},"lang":"pl","stats":{"time":"2026-11-05 11:50 CET","day":"2026-11-04","rows":[["","suma","2757995","100.00 %","6510248","100.00 %","2.36","+1467","+7614","+27206","+192512"],[1,"pl","2317405","84.02 %","5439604","83.55 %","2.35","+1194",' |
| INFO | dns.pl | API /api/count-deleted-domains → HTML (SPA-catch-all) | len=17 |
| INFO | dns.pl | API /api/registrars-services otwarte (application/json) | len=78 head='["transfer","ipv6","prio","bookblocked","dnssec","dnssecready","registrylock"]' |
| INFO | dyzurnet.pl | /api status 404 | ct=text/html len=39082 loc= head='<!DOCTYPE html><html id="__next_error__"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width,' |
| INFO | science.nask.pl | API /api/search?q=test kontrakt | status=400 head='{"error":"Query must be at least 3 characters"}' |
| INFO | science.nask.pl | API /api/contact kontrakt | status=405 head='{"error":"Method not allowed"}' |
