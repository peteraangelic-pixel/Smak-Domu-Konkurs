import sys, logging, json, re, glob
sys.path.insert(0, '/tmp/ae'); sys.path.insert(0, '/tmp/agx')
logging.disable(logging.WARNING)
from pathlib import Path
ENVDIR = Path('/home/user/Smak-Domu-Konkurs/arc-agi-3/games/environment_files')

# 1) z zrodel gier: pozycje sprite'ow sys_click i ich placementy
def sprite_positions(gid):
    src = (ENVDIR/gid/gid/f"{gid}.py").read_text()
    # znajdz placementy: wywolania typu Sprite(...)? / placements w Level(...)? — heurystyka:
    # szukaj wyraznych wspolrzednych przy tagach sys_click w kodzie placements
    pos = []
    for m in re.finditer(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', src):
        pos.append((int(m.group(1)), int(m.group(2))))
    return pos[:200]

# 2) weryfikacja na silniku: klik w pozycje zrodlowe
from arc_agi import Arcade, OperationMode, LocalEnvironmentWrapper
from arcengine import GameAction, GameState
arcade = Arcade(operation_mode=OperationMode.OFFLINE, environments_dir=str(ENVDIR))
envs = {e.game_id.split('-')[0]: e for e in arcade.available_environments}
LOG = logging.getLogger("x")

out = {}
for gid in sorted(envs):
    src = ENVDIR/gid/gid/f"{gid}.py"
    if not src.exists(): continue
    txt = src.read_text()
    n_click = txt.count('sys_click')
    env = LocalEnvironmentWrapper(environment_info=envs[gid], logger=LOG, scorecard_id='op', include_frame_data=False)
    fd = env.reset(); acts=1; last=fd.levels_completed if fd else 0; clears=[]
    avail = fd.available_actions if fd else []
    cleared_by_click = 6 in (avail or [])
    if cleared_by_click:
        cands = sprite_positions(gid)
        for (x,y) in cands:
            fd = env.step(GameAction.ACTION6, {'x': min(x,63), 'y': min(y,63)}); acts+=1
            if fd is None: continue
            if fd.levels_completed>last:
                clears.append((last+1, acts)); last=fd.levels_completed
            if fd.state==GameState.WIN or acts>=60: break
            if fd.state==GameState.GAME_OVER: env.reset(); acts+=1
    else:
        # klawiszowe: sprobuj sekwencji 1..5 x 12 (maly budzet — tylko level 1 test)
        for act in [GameAction.ACTION1,GameAction.ACTION2,GameAction.ACTION3,GameAction.ACTION4,GameAction.ACTION5]:
            for i in range(12):
                fd = env.step(act); acts+=1
                if fd is None: break
                if fd.levels_completed>last:
                    clears.append((last+1, acts)); last=fd.levels_completed
                if fd.state==GameState.WIN: break
                if fd.state==GameState.GAME_OVER: env.reset(); acts+=1
            if fd and fd.state==GameState.WIN: break
            if last>0: break
    out[gid]={'tag_sys_click':n_click, 'actions':acts, 'levels':last, 'clears':clears[:6]}
    print(f"{gid:6} sys_click={n_click:>3} akcje={acts:>3} poziomy={last} clears={clears[:4]}")
json.dump(out, open('/tmp/openers.json','w'), indent=1)
