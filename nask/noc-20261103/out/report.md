# Nocny skan NASK — raport automatyczny

bieg: 2026-11-03T23:19:39+00:00 | żądań: 229 | limit: 4.5 req/s (regulamin ≤5) | GET-only, bez auth, 12 hostów z §5

| sev | host | co | dowód |
|---|---|---|---|
| MED | dataannotation.pllum.org.pl | ekspozycja /api/v1/users | status=307 ct= len=0 head='' |
| MED | dataannotation.pllum.org.pl | ekspozycja /api/users | status=404 ct=application/json len=22 head='{"detail":"Not Found"}' |
| MED | dataannotation.pllum.org.pl | ekspozycja /api/v1/config | status=404 ct=application/json len=22 head='{"detail":"Not Found"}' |
| NEARMISS | dns.pl | status-inny /.git/HEAD | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /.env | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /.env.local | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /config.json | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /.svn/entries | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /server-status | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dns.pl | status-inny /actuator/env | status=200 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /.git/HEAD | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /.env | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /.env.local | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /config.json | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /backup.zip | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /.svn/entries | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /.well-known/security.txt | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /api/v1/users | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /api/users | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /api/v1/config | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /swagger.json | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | status-inny /openapi.json | status=404 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | dyzurnet.pl | kandydat z robots /api/ | status=308 ct= len=4 |
| NEARMISS | oad.nask.pl | status-inny /.git/HEAD | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | oad.nask.pl | status-inny /.env | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | oad.nask.pl | status-inny /.env.local | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | oad.nask.pl | status-inny /.svn/entries | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | pllum.org.pl | status-inny /.git/HEAD | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | pllum.org.pl | status-inny /.env | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | pllum.org.pl | status-inny /.env.local | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | pllum.org.pl | status-inny /.svn/entries | status=403 vs base=404 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /.git/HEAD | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /.env | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /.env.local | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /config.json | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /backup.zip | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /.svn/entries | status=403 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /.well-known/security.txt | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /api/v1/users | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /api/users | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /api/v1/config | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /swagger.json | status=500 vs base=200 (HTML — raczej catch-all/router) |
| NEARMISS | zglos-dezinformacje.nask.pl | status-inny /openapi.json | status=500 vs base=200 (HTML — raczej catch-all/router) |
| INFO | 116sos.pl | alive 502 len=150 | {"server": "", "azure": false, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "", "powered": "", "cookies": ["stickounet"]} |
| INFO | bezpiecznewybory.pl | alive 403 len=369 | {"server": "", "azure": false, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "", "powered": "", "cookies": []} |
| INFO | bezpiecznewybory.pl | UA-browser status=403 len=369 | ct=text/html head='<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n</HEAD><BODY>\n<H1>Access Denied</H1>\n \nYou don\'t have permission to access "http&#58;&#47;&#47;bezpiecznewyb' |
| INFO | bezpiecznymiesiac.pl | alive 200 len=96343 | {"server": "", "azure": true, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "CONFIG_NOCACHE", "powered": "", "cookies": ["Path"]} |
| INFO | dataannotation.pllum.org.pl | alive 200 len=713 | {"server": "", "azure": true, "envoy": true, "nextjs": false, "cloudflare": false, "cache": "CONFIG_NOCACHE", "powered": "", "cookies": []} |
| INFO | dns.pl | alive 200 len=51148 | {"server": "", "azure": false, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "", "powered": "", "cookies": ["SESID"]} |
| INFO | dns.pl | ekspozycja /.well-known/security.txt | status=307 ct= len=0 head='' |
| INFO | dyzurnet.pl | alive 200 len=106937 | {"server": "cloudflare", "azure": false, "envoy": false, "nextjs": false, "cloudflare": true, "cache": "", "powered": "", "cookies": ["locale"]} |
| INFO | dyzurnet.pl | robots.txt ścieżki | /api/ |
| INFO | dyzurnet.pl | sitemap.xml: 1 URL-i | https://dyzurnet.pl/pl |
| INFO | nask.pl | alive 302 len=0 | {"server": "", "azure": false, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "", "powered": "", "cookies": []} |
| INFO | oad.nask.pl | alive 200 len=75666 | {"server": "", "azure": true, "envoy": true, "nextjs": false, "cloudflare": false, "cache": "CONFIG_NOCACHE", "powered": "", "cookies": []} |
| INFO | pllum.org.pl | alive 200 len=133988 | {"server": "", "azure": true, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "CONFIG_NOCACHE", "powered": "", "cookies": ["x-ms-routing-name"]} |
| INFO | science.nask.pl | alive 200 len=161608 | {"server": "", "azure": false, "envoy": false, "nextjs": true, "cloudflare": false, "cache": "", "powered": "", "cookies": ["stickounet"]} |
| INFO | secure.edu.pl | nie odpowiada (HTTPS/443) | {"ts": "2026-11-03T23:15:26+00:00", "module": "sweep", "host": "secure.edu.pl", "path": "/", "url": "https://secure.edu.pl/", "error": "URLError: <urlopen error timed out>", "t": 16.43} |
| INFO | zglos-dezinformacje.nask.pl | alive 200 len=43912 | {"server": "", "azure": true, "envoy": false, "nextjs": false, "cloudflare": false, "cache": "CONFIG_NOCACHE", "powered": "", "cookies": []} |
| INFO | zglos-dezinformacje.nask.pl | sitemap.xml: 2 URL-i | https://zglos-dezinformacje.nask.pl/; https://zglos-dezinformacje.nask.pl/en |
