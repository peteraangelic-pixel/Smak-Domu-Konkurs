# Nocny skan NASK — BIEG 7 (dns.pl: D1/D2 kontrakty + XFH cache hunt)

bieg: 2026-11-05T11:18:08+00:00 | żądań: 10 | limit 4.5 rps | GET+lookup-POST, 1 host §5

| sev | co | dowód |
|---|---|---|
| MED | dns.pl: D1 bez-captcha: 200 text/html (sprawdzić treść: dane > publiczny whois?) | len=51220 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n<script type="text/javascript">\n  var _event_transid=\'2072802415\';\n</script>\n\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device-width, initial-scale=1"/>\n    <title>DNS \| Krajowy ' |
| MED | dns.pl: D1 pusta-captcha: 200 text/html (sprawdzić treść: dane > publiczny whois?) | len=51210 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n<script type="text/javascript">\n  var _event_transid=\'2072802416\';\n</script>\n\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device-width, initial-scale=1"/>\n    <title>DNS \| Krajowy ' |
| MED | dns.pl: D1-form: 200 text/html; charset=UTF-8 | len=51223 head=b'<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n<script type="text/javascript">\n  var _event_transid=\'2072802418\';\n</script>\n\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device-width, initial-scale=1"/>\n    <title>DNS \| Krajowy ' |
| INFO | dns.pl: D2: domain-browser 200 bez tokenu (text/html) | len=51229 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n<script type="text/javascript">\n  var _event_transid=\'2072802417\';\n</script>\n\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device-width, initial-scale=1"/>\n    <title>DNS \| Krajowy ' |
