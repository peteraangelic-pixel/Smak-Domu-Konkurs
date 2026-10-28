import sys, logging, json, time
sys.path.insert(0, '/tmp/ae'); sys.path.insert(0, '/tmp/agx')
logging.disable(logging.WARNING)
from arc_agi import Arcade, OperationMode, LocalEnvironmentWrapper
from arcengine import GameAction, GameState

ENV = '/home/user/Smak-Domu-Konkurs/arc-agi-3/games/environment_files'
arcade = Arcade(operation_mode=OperationMode.OFFLINE, environments_dir=ENV)
envs = {e.game_id: e for e in arcade.available_environments}
print("dostepne gry:", sorted(envs)[:30])

LOG = logging.getLogger("p"); LOG.addHandler(logging.NullHandler())
def mk(gid):
    return LocalEnvironmentWrapper(environment_info=envs[gid], logger=LOG, scorecard_id="probe1", seed=0, include_frame_data=False)

SIMPLE = [GameAction.ACTION1, GameAction.ACTION2, GameAction.ACTION3, GameAction.ACTION4, GameAction.ACTION5, GameAction.ACTION7]

def levels_of(fd):
    return int(getattr(fd, 'levels_completed', 0) or 0)

def state_of(fd):
    return str(getattr(fd, 'state', ''))

results = {}
t0 = time.time()
for gid in sorted(envs):
    env = mk(gid)
    fd = env.reset()
    if fd is None:
        results[gid] = {'err': 'reset fail'}; continue
    actions = 0
    clears = []          # (level_no, akcje_cumulative, protokol, nazwa)
    lvl0 = levels_of(fd)
    last_lvl = lvl0
    done = state_of(fd) == 'WIN'
    # PROTOKOL A: kazda prosta akcja x40 (kod, bez LLM)
    for act in SIMPLE:
        for i in range(40):
            fd = env.step(act)
            actions += 1
            if fd is None: break
            L = levels_of(fd)
            if L > last_lvl:
                for k in range(last_lvl+1, L+1): clears.append((k, actions, 'repeat', act.name))
                last_lvl = L
            if state_of(fd) == 'WIN': done = True; break
        if done: break
    # PROTOKOL B: sweep klikniec 8x8 (x,y=4,12,...60)
    if not done:
        for yy in range(4, 64, 8):
            for xx in range(4, 64, 8):
                fd = env.step(GameAction.ACTION6, {'x': xx, 'y': yy})
                actions += 1
                if fd is None: continue
                L = levels_of(fd)
                if L > last_lvl:
                    for k in range(last_lvl+1, L+1): clears.append((k, actions, 'click', f'{xx},{yy}'))
                    last_lvl = L
                if state_of(fd) == 'WIN': done = True; break
            if done: break
    results[gid] = {'actions': actions, 'levels_cleared_by_protocol': len(clears),
                    'final_state': state_of(fd) if fd else '?', 'clears': clears[:12], 'done': done}
    print(f"{gid}: akcje={actions:>4} zdejmiete_poziomy={len(clears):>2} stan={state_of(fd) if fd else '?'} pierwsze: {clears[:4]}")
print(f"czas: {time.time()-t0:.1f}s")
json.dump(results, open('/tmp/probe1.json','w'), indent=1)
