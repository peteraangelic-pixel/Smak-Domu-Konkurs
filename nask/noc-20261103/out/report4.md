# Nocny skan NASK — BIEG 4 (probe odkrytych tras API)

bieg: 2026-11-03T23:14:19+00:00 | żądań: 16 | limit 4.5 rps | GET-only, bez auth, 12 hostów §5

| sev | host | co | dowód |
|---|---|---|---|
| INFO | dataannotation.pllum.org.pl | /admin/ status 200 | ct=text/html len=713 loc= head='<!doctype html>\n<html lang="en">\n  <head>\n    <meta charset="UTF-8" />\n    <meta name="viewport" content="width=device-w' |
| INFO | dataannotation.pllum.org.pl | /api/v1/ status 404 | ct=application/json len=22 loc= head='{"detail":"Not Found"}' |
| INFO | dns.pl | API /api/zone-stats otwarte (application/json) | len=11759 head='{"errors":{},"lang":"pl","stats":{"time":"2026-11-04 00:13 CET","day":"2026-11-03","rows":[["","suma","2756528","100.00 %","6506855","100.00 %","2.36","+1085","+7606","+26125","+191046"],[1,"pl","2316211","84.03 %","5436873","83.56 %","2.35","+893","' |
| INFO | dns.pl | API /api/count-deleted-domains → HTML (SPA-catch-all) | len=17 |
| INFO | dns.pl | API /api/registrars-services otwarte (application/json) | len=78 head='["transfer","ipv6","prio","bookblocked","dnssec","dnssecready","registrylock"]' |
| INFO | dyzurnet.pl | /api status 404 | ct=text/html len=38981 loc= head='<!DOCTYPE html><html id="__next_error__"><head><meta charSet="utf-8"/><meta name="viewport" content="width=device-width,' |
| INFO | science.nask.pl | API /api/search?q=test kontrakt | status=400 head='{"error":"Query must be at least 3 characters"}' |
| INFO | science.nask.pl | API /api/contact kontrakt | status=405 head='{"error":"Method not allowed"}' |
