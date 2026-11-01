"""Offline prototype: discriminate executable hypotheses using observed transitions.

No game identifiers, engine calls, hidden goals or action execution. Integration
with Duck and LLM-generated models is still required before a quality trial.
"""
from collections import Counter
import math


def freeze(value):
    if isinstance(value, dict):
        return ('dict', tuple(sorted(((freeze(k), freeze(v)) for k,v in value.items()), key=repr)))
    if isinstance(value, (list, tuple)):
        return tuple(map(freeze, value))
    if isinstance(value, (set, frozenset)):
        return frozenset(map(freeze, value))
    hash(value)
    return value


def validate(hypotheses, transitions):
    """Each hypothesis supplies encode(frame), step(state, action).

    Each transition is (before_frame, action, after_frame), all genuinely
    observed. No prediction is silently substituted for an observation.
    An incomplete/erroring model cannot pass a validation gate.
    """
    print('HYPOTHESIS_VALIDATE models='+str(len(hypotheses))+' transitions='+str(len(transitions)))
    reports=[]
    for model in hypotheses:
        correct=errors=0; mismatches=[]
        for before, action, after in transitions:
            try:
                state=model['encode'](before)
                predicted=model['step'](state, action)
                if predicted is None:predicted=state
                actual=model['encode'](after)
                equal=freeze(predicted)==freeze(actual)
                correct+=int(equal)
                if not equal:mismatches.append({'action':action,'predicted':predicted,'actual':actual})
            except Exception as exc:
                errors+=1;mismatches.append({'action':action,'error':type(exc).__name__})
        reports.append({'name':model['name'],'checked':len(transitions),'correct':correct,
                        'errors':errors,'validated':bool(transitions) and correct==len(transitions) and not errors,
                        'mismatches':mismatches})
    return reports


def choose_probe(hypotheses, frame, valid_actions, costs=None):
    """Return highest disagreement per explicit cost; abstain on model errors.

    Hypotheses must encode states in a COMMON comparison schema. Caller must
    supply allowed actions; this module never invents mouse coordinates. It
    cannot certify action safety and does not execute its recommendation.
    """
    print('HYPOTHESIS_PROBE models='+str(len(hypotheses))+' actions='+str(len(valid_actions)))
    if len(hypotheses)<2:return None
    ranked=[]
    for i,action in enumerate(valid_actions):
        predictions=[]
        try:
            for model in hypotheses:
                state=model['encode'](frame)
                predicted=model['step'](state,action)
                predictions.append(freeze(state if predicted is None else predicted))
            cost=1.0 if costs is None else float(costs[i])
            if not math.isfinite(cost) or cost<=0:continue
        except Exception:
            continue
        counts=Counter(predictions);n=len(predictions)
        entropy=-sum((c/n)*math.log2(c/n) for c in counts.values())
        if entropy>0:ranked.append((entropy/cost,-i,action,entropy))
    if not ranked:return None
    score,_,action,entropy=max(ranked,key=lambda x:x[:2])
    return {'action':action,'disagreement_bits':entropy,'information_per_cost':score}
