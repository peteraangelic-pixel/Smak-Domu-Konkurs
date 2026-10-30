"""Probe v18's default mouse vocabulary on public initial boards, one job per game."""
from concurrent.futures import ProcessPoolExecutor
import copy, json, re, sys
from pathlib import Path
from types import SimpleNamespace
D = Path(__file__).resolve().parent
sys.path.insert(0, str(D.parent / 'analysis'))
from sweep2 import load_game, ActionInput, RESET, MOUSE, frame_of
from clicks import wm_click_actions

def probe(path):
    cls = re.search(r'^class (\w+)\(ARCBaseGame\)',path.read_text(encoding='utf8'),re.M)[1]
    game=load_game(str(path),cls)
    fd=game.perform_action(ActionInput(id=RESET),raw=True)
    if 6 not in fd.available_actions: return {'game':path.stem,'mouse':False}
    frame=frame_of(fd)
    actions=wm_click_actions(SimpleNamespace(_grid=frame.tolist(),level=0),[])
    effects=set()
    for act in actions:
        child=copy.deepcopy(game)
        result=child.perform_action(ActionInput(id=MOUSE,data={'x':act['col'],'y':act['row']}),raw=True)
        observed=frame_of(result)
        if (observed!=frame).any(): effects.add(observed.tobytes())
    return {'game':path.stem,'mouse':True,'clicks':len(actions),'distinct_changes':len(effects)}

if __name__=='__main__':
    paths=sorted((D.parent/'games/environment_files').rglob('*.py'))
    with ProcessPoolExecutor(max_workers=16) as pool: rows=list(pool.map(probe,paths))
    (D/'click-probe.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows))
