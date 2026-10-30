"""Read-only public notebook discovery. Never uploads or submits to Kaggle."""
from concurrent.futures import ThreadPoolExecutor
import csv
import io
import json
from pathlib import Path
import subprocess

COMP = 'arc-prize-2026-arc-agi-3'
OUT = Path('research')
OUT.mkdir(exist_ok=True)
# Discovery handles from dated public ARC3 roster observations, not authorship
# evidence for any private agent. Missing roster identities remain explicit.
USERS = '''threerabbits dlorah driessmit1 pressman1 stefano1283 infinitecreativity
jeroencottaar xiaoz259 ngyzly mitubant keithtyser dzjiann markbarney sonphamorg
scizical gklambauer fses91 dwellement0baser lukasaichberger yktori michaeltgao grigoriyzatravkin aizealotwu deepdreamer florenciasolange
cpmpml darraghdog eladsarafian galkaplun sorokin yeyinzhu titericz
isakatsuyoshi konbu17 pompom555 refv00 tanakaai24 tk256ailab ttyn4519 yuto0712'''.split()


def command(args, target):
    try:
        result = subprocess.run(['kaggle', *args], capture_output=True, text=True, timeout=90)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result.stdout + '\n' + result.stderr)
        return {'returncode': result.returncode, 'stdout': result.stdout}
    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'stdout': ''}


command(['competitions', 'leaderboard', '-c', COMP, '--show'], OUT/'leaderboard.txt')
command(['competitions', 'submissions', '-c', COMP, '--csv'], OUT/'own-submissions.csv')


def listing(user):
    result = command(['kernels', 'list', '--user', user, '--competition', COMP,
                      '--page-size', '100', '--csv'], OUT/'users'/f'{user}.txt')
    result['user'] = user
    return result


with ThreadPoolExecutor(max_workers=4) as pool:
    listings = list(pool.map(listing, USERS))
refs = set()
for result in listings:
    if result.get('returncode') == 0:
        try:
            for row in csv.DictReader(io.StringIO(result['stdout'])):
                ref = row.get('ref', '')
                if '/' in ref:
                    refs.add(ref)
        except csv.Error:
            pass


def pull(ref):
    target = OUT/'sources'/ref.split('/')[0]/ref.split('/')[1]
    result = command(['kernels', 'pull', ref, '--metadata', '--path', str(target)], target/'pull.log')
    return {'ref': ref, 'returncode': result.get('returncode'), 'error': result.get('error')}


with ThreadPoolExecutor(max_workers=4) as pool:
    pulls = list(pool.map(pull, sorted(refs)[:60]))
summary = {'users': [{k: v for k, v in r.items() if k != 'stdout'} for r in listings],
           'public_refs': sorted(refs), 'pulls': pulls,
           'limits': 'First 100 public notebooks per user; first 60 sources downloaded; no private sources.'}
(OUT/'summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
