"""Add an immutable review bundle to authorized peer branches; never force refs."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = 'arc-agi-3/peer-review/codex-v3-slim-20261101'
TARGETS = {
    'Pokemon': ['arena/a450b00f-pokemon', 'arena/c87f7a48-pokemon', 'arena/7911f950-pokemon'],
    'Gemma-konkurs': ['arena/c4eeb067-gemma-konkurs', 'arena/6d081d52-gemma-konkurs'],
    'Smak-Domu-Konkurs': ['arena/5ed750ef-smak-domu-konkurs'],
}

def api(endpoint, method='GET', payload=None):
    args = ['gh', 'api', endpoint, '--method', method]
    if payload is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(payload) if payload is not None else None,
                            text=True, capture_output=True, encoding='utf8', check=True)
    return json.loads(result.stdout)

def publish(repo_name, files):
    repo = 'peteraangelic-pixel/' + repo_name
    base = 'repos/' + repo
    blobs = {name: api(base+'/git/blobs', 'POST', {
        'content': base64.b64encode(data).decode(), 'encoding': 'base64'})['sha']
        for name, data in files.items()}
    results = []
    for branch in TARGETS[repo_name]:
        # Read the current parent immediately before creating this branch's commit.
        parent = api(base+'/git/ref/heads/'+branch)['object']['sha']
        old_tree = api(base+'/git/commits/'+parent)['tree']['sha']
        tree = api(base+'/git/trees', 'POST', {'base_tree': old_tree, 'tree': [
            {'path': DEST+'/'+name, 'mode': '100644', 'type': 'blob', 'sha': sha}
            for name, sha in blobs.items()]})['sha']
        if tree == old_tree:
            results.append({'repo': repo, 'branch': branch, 'commit': parent, 'unchanged': True})
            continue
        commit = api(base+'/git/commits', 'POST', {
            'message': 'Add Codex v3-slim candidate and evidence for peer review',
            'tree': tree, 'parents': [parent]})['sha']
        # Non-fast-forward rejection preserves concurrent work by other sessions.
        api(base+'/git/refs/heads/'+branch, 'PATCH', {'sha': commit, 'force': False})
        verified = api(base+'/git/trees/'+tree+'?recursive=1')['tree']
        actual = {x['path']: x['sha'] for x in verified}
        assert all(actual[DEST+'/'+name] == sha for name, sha in blobs.items())
        row = {'repo': repo, 'branch': branch, 'parent': parent, 'commit': commit,
               'verified_files': len(blobs), 'url': f'https://github.com/{repo}/tree/{commit}/{DEST}'}
        results.append(row)
        print(json.dumps(row), flush=True)
    return results

def main():
    package = ROOT/'peer-review/codex-v3-slim-20261101'
    package.mkdir(parents=True, exist_ok=True)
    sources = {
        'agent.ipynb': ROOT/'duck-lab-candidates/v3-slim/agent.ipynb',
        'kernel-metadata.json': ROOT/'duck-lab-candidates/v3-slim/kernel-metadata.json',
        'MANIFEST.json': ROOT/'duck-lab-candidates/v3-slim/MANIFEST.json',
        'verification.json': ROOT/'analysis/v3-slim-20261101/verification.json',
        'RUN.json': ROOT/'analysis/v3-slim-20261101/RUN.json',
        'NEXT-HYPOTHESIS.md': ROOT/'analysis/v3-slim-20261101/NEXT-HYPOTHESIS.md',
        'CONTROL-RESULT.md': ROOT/'analysis/V3-TARGET-RESULT-20261031.md',
    }
    for name, source in sources.items():
        (package/name).write_bytes(source.read_bytes())
    assert hashlib.sha256((package/'agent.ipynb').read_bytes()).hexdigest() == '9156966a191604eb7a0285aecd4d4c9ba0bef557232dc0315d2cbe63bea95458'
    (package/'README.md').write_text('''# Kandydat Codex v3-slim do niezależnej oceny — 1 listopada 2026

## Status
Eksperyment, NIE potwierdzona poprawa i NIE submisja konkursowa. W chwili przygotowania pakietu prywatny test docelowego modelu nadal trwał. RUN.json jest snapshotem, nie bieżącym statusem. Nie przypisywać temu kodowi historycznych wyników kontroli.

## Co dokładnie zmieniono
Dokładna odzyskana v3 (SHA bazowego notebooka w MANIFEST.json), jedyna zmiana polityki: ARC3_MEMORY_SECTIONS off -> slim. Pozostaje bieżący World model i Plan. To upstream mechanizm, nie lalalia solved-level memory. Model, roster 10 publicznych gier, 48 min/gra, concurrency 10 i konfiguracja serwowania identyczne z kontrolą. Zmiana nazwy wariantu jest opisana w manifeście. Bez template, routera, nowych capów, recovery lub sterowania po game ID.

agent.ipynb SHA256: 9156966a191604eb7a0285aecd4d4c9ba0bef557232dc0315d2cbe63bea95458

## Dowody i ograniczenia
verification.json: rzeczywisty ToolAgent niesie World model/Plan w slim, usuwa je w off; 34 źródła inference identyczne z bazą, czysty łańcuch patchy. To kontrola infrastruktury, nie pomiar jakości. Kontrola na docelowym Flash-Next miała 33 ukończenia i 27.49667 w publicznym smoke; pojedynczy historyczny przebieg nie dowodzi przewagi nowego wariantu. Kod pamięci ukończonych poziomów 28.40/32 i recovery 17.11/25 odrzucono — nie scalać ich automatycznie.

## O co prosimy przy ocenie
Sprawdzić faktyczną aktywację sekcji w promptach, ukończenia per gra, nowe zera, błędy, tokeny i regresje. Obiecujący wynik wymaga świeżej kontroli lub sparowanej replikacji. W NEXT-HYPOTHESIS.md są tropy z logów oraz jawna korekta: action zwraca dict, executed to bool, executed_actions to lista. Nie wyłączać zabezpieczeń stale-state w celu zmniejszenia liczby błędów.

## Własne eksperymenty
Nie nadpisywać oryginalnego sluga petersharps/arc3-duck-codex-v3-slim-1101 ani jego wersji 1. kernel-metadata.json zachowuje oryginalną konfigurację wyłącznie do odtworzenia; przed własnym push zmienić id i title na odrębny slug. Nie wysyłać do konkursu bez zgody użytkownika. Zachować ten pakiet jako kontrolę i ulepszenia zapisać obok, z nowym hashem, opisem zmiany i własnym pomiarem. Sam commit pakietu nie uruchamia sesji innych AI.

## Aktualne wyniki i surowe dane
Kolektor GitHub Actions: https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/actions/runs/41288053823
Notebook prywatny: https://www.kaggle.com/code/petersharps/arc3-duck-codex-v3-slim-1101
Nasza gałąź z aktualizowanym dziennikiem i surowymi wynikami: https://github.com/peteraangelic-pixel/Smak-Domu-Konkurs/tree/codex/arc-local-lab-v18-20261030/arc-agi-3/analysis
''', encoding='utf8')
    files = {p.name: p.read_bytes() for p in package.iterdir() if p.is_file()}
    records = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for rows in pool.map(lambda repo: publish(repo, files), TARGETS):
            records.extend(rows)
    out = ROOT/'analysis/v3-slim-20261101/PEER-DISTRIBUTION.json'
    out.write_text(json.dumps({'package': DEST, 'targets': records}, indent=2), encoding='utf8')

if __name__ == '__main__':
    main()
