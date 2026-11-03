# Nocny skan NASK — BIEG 5 (kontrakty API: downloadFile, domain-browser, search)

bieg: 2026-11-03T23:26:48+00:00 | żądań: 9 | limit 4.5 rps | GET-only, read-only

| sev | host | co | dowód |
|---|---|---|---|
| INFO | dns.pl | /api/domain-browser/nask.pl status 404 | ct=text/html len=40909 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device' |
| INFO | dns.pl | /api/who-is-xml/nask.pl status 404 | ct=text/html len=40908 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device' |
| INFO | dns.pl | /api/who-is-xml?domain=nask.pl status 404 | ct=text/html len=40918 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device' |
| INFO | dns.pl | /api/domain-browser?domain=nask.pl status 404 | ct=text/html len=40903 head='<!DOCTYPE html>\n<html lang="pl"\n    >\n<head>\n    <meta charset="utf-8"/>\n    <meta name="viewport" content="width=device' |
| INFO | science.nask.pl | /api/downloadFile?file=README.txt zwisa >25s (dlugotrwala operacja?) | URLError:<urlopen error timed out> t>25s |
| INFO | science.nask.pl | /api/downloadFile?name=test.txt status 400 | ct=application/json len=27 disp= head='{"error":"Invalid file id"}' |
| INFO | science.nask.pl | /api/search q=abc%27 status 400 | refleksja=False head='{"error":"Query must be at least 3 characters"}' |
