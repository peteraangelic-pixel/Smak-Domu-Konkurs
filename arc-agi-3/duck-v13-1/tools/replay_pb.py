import sys, logging, json
sys.path.insert(0, '/tmp/ae'); sys.path.insert(0, '/tmp/agx')
logging.disable(logging.WARNING)
from arc_agi import Arcade, OperationMode, LocalEnvironmentWrapper
from arcengine import GameAction, GameState
ENV = './games/environment_files'  # sciezka do katalogu 25 gier
arcade = Arcade(operation_mode=OperationMode.OFFLINE, environments_dir=ENV)
envs = {e.game_id.split('-')[0]: e for e in arcade.available_environments}
LOG = logging.getLogger("x")
pb = json.load(open('/tmp/v13m/playbook.json'))['games']
NAME = {"ACTION1": GameAction.ACTION1, "ACTION2": GameAction.ACTION2, "ACTION3": GameAction.ACTION3,
        "ACTION4": GameAction.ACTION4, "ACTION5": GameAction.ACTION5, "ACTION6": GameAction.ACTION6,
        "ACTION7": GameAction.ACTION7}
ok_all, all_lvl = 0, 0
for gid, g in pb.items():
    env = LocalEnvironmentWrapper(environment_info=envs[gid], logger=LOG, scorecard_id='rp', include_frame_data=False)
    fd = env.reset(); last = 0; confirmed = []
    for lvl_no in sorted(g['levels'], key=int):
        entry = g['levels'][lvl_no]
        cleared = False
        for a in entry['actions']:
            nm, data = a['name'], a.get('data') or {}
            fd = env.step(NAME[nm], data if nm == "ACTION6" else None)
            if fd is None: break
            if fd.levels_completed > last:
                last = fd.levels_completed; confirmed.append(last); cleared = True
            if fd.state == GameState.WIN: break
        if not cleared: break
    ok_all += len(confirmed); all_lvl += len(g['levels'])
    print(f"{gid:6} poziomy_zgloszone={sorted(int(k)+1 for k in g['levels'])} potwierdzone={confirmed} (last={last})")
print(f"\nWYNIK: {ok_all}/{all_lvl} poziomów playbooka potwierdzonych na PRAWDZIWYM silniku (arcengine 0.9.3 / arc-agi 0.9.9)")
