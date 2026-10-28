import sys, logging, json, time
sys.path.insert(0, '/tmp/ae'); sys.path.insert(0, '/tmp/agx')
logging.disable(logging.WARNING)
from arc_agi import Arcade, OperationMode, LocalEnvironmentWrapper
from arcengine import GameAction, GameState

ENV = '/home/user/Smak-Domu-Konkurs/arc-agi-3/games/environment_files'
arcade = Arcade(operation_mode=OperationMode.OFFLINE, environments_dir=ENV)
envs = {e.game_id: e for e in arcade.available_environments}
LOG = logging.getLogger("p"); LOG.addHandler(logging.NullHandler())
SIMPLE = [GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4, GameAction.ACTION5, GameAction.ACTION7]
CAP = 900

def run(gid):
    env = LocalEnvironmentWrapper(environment_info=envs[gid], logger=LOG, scorecard_id="p2", seed=0, include_frame_data=False)
    fd = env.reset(); acts = 1; last = fd.levels_completed if fd else 0
    clears = []; won = False; dead_resets = 0
    def punch(a, data=None):
        nonlocal fd, acts, last, won
        fd = env.step(a, data) if data is not None else env.step(a)
        acts += 1
        if fd is None: return
        if fd.levels_completed > last:
            for k in range(last+1, fd.levels_completed+1): clears.append((k, acts))
            last = fd.levels_completed
        if fd.state == GameState.WIN: won = True
    for act in SIMPLE:
        avail = fd.available_actions if fd else []
        # numer akcji w available_actions to inty 0..7? ACTION1=1...
        if hasattr(act, 'value') and avail and (act.value if isinstance(act.value,int) else 0) not in avail:
            continue
        for rep in range(150):
            punch(act)
            if fd and fd.state == GameState.GAME_OVER:
                env.reset(); acts += 1; dead_resets += 1
            if won or acts >= CAP: break
        if won or acts >= CAP: break
    if not won:
        for yy in range(4, 64, 8):
            for xx in range(4, 64, 8):
                punch(GameAction.ACTION6, {'x': xx, 'y': yy})
                if fd and fd.state == GameState.GAME_OVER:
                    env.reset(); acts += 1; dead_resets += 1
                if won or acts >= CAP: break
            if won or acts >= CAP: break
    st = str(fd.state.value) if fd else '?'
    return {'actions': acts, 'levels': last, 'clears': clears[:10], 'state': st, 'dead_resets': dead_resets, 'won': won}

out = {}; t0 = time.time()
for gid in sorted(envs):
    r = run(gid); out[gid] = r
    print(f"{gid:18} akcje={r['actions']:>4} poziomy={r['levels']:>2} stany={r['state']:<14} resety={r['dead_resets']:>3} W={r['won']} pierwsze={r['clears'][:5]}")
print(f"czas {time.time()-t0:.1f}s")
json.dump(out, open('/tmp/probe2.json','w'), indent=1)
