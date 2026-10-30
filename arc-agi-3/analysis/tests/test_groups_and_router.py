import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from group_regressions import compare
from observation_router import route
from observation_router import install


def row(game, family, score):
    return dict(game=game, seed=1, model='same-model', budget={'tokens':100}, game_sha256=game,
                families=['all',family], levels_completed=1, rhae_score_pct=score, error=None, api_errors=0)


def test_group_regression_detected_despite_positive_overall_mean():
    a=[row('a','mouse_only',10),row('b','keyboard_only',10)]
    b=[row('a','mouse_only',30),row('b','keyboard_only',5)]
    result=compare(a,b)
    assert result['groups']['all']['mean_score_delta']>0
    assert not result['no_group_score_regressions']
    assert result['groups']['keyboard_only']['regressed_games']==['b']


def test_missing_corpus_and_changed_budget_are_rejected():
    a=[row('a','mouse_only',10)]
    with pytest.raises(ValueError): compare(a,[])
    b=copy.deepcopy(a);b[0]['budget']={'tokens':200}
    with pytest.raises(ValueError,match='budget'):compare(a,b)


def test_router_depends_on_legal_observations():
    frame=NS(level=1,grid=((0,0),(0,0)))
    assert route(frame,[],['UP','DOWN'])[0]=='spatial'
    assert route(frame,[],['MOUSE'])[0]=='mouse_probe'
    # Four observations of one pixel toggling; no IDs, baselines or source.
    history=[NS(frame=NS(level=1,grid=((i%2,0),(0,0)))) for i in range(4)]
    assert route(frame,history,['MOUSE'])[0]=='tiny_changes'


def test_router_never_infers_tiny_motion_across_level_boundaries():
    frame=NS(level=2,grid=((0,),))
    history=[NS(frame=NS(level=i+1,grid=((i%2,),))) for i in range(4)]
    assert route(frame,history,['MOUSE'])[0]=='mouse_probe'


def test_repeated_inspection_guard_preserves_action_and_changed_observation(tmp_path):
    import json
    class Agent:
        def _build_user_prompt(self,*args,**kwargs):return 'base'
        def _run_python_tool(self,state_path,arguments):return arguments['code']
    install(Agent)
    agent=Agent()
    state=tmp_path/'state.json'
    state.write_text(json.dumps({'current_frame':{'level':1,'grid':[[0]]}}))
    inspect={'code':'print(1)'}
    assert agent._run_python_tool(state,inspect)=='print(1)'
    assert agent._run_python_tool(state,inspect)=='print(1)'
    assert 'OBSERVATION ROUTER' in agent._run_python_tool(state,inspect)
    for _ in range(5):
        assert agent._run_python_tool(state,{'code':'action("UP")'})=='action("UP")'
    state.write_text(json.dumps({'current_frame':{'level':2,'grid':[[0]]}}))
    assert agent._run_python_tool(state,inspect)=='print(1)'
