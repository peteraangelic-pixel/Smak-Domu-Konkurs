"""Experimental Duck prompt routing using only legal observations/history.

No game IDs, source inspection, baselines, engine cloning or solved paths.
The router supplies a falsifiable exploration strategy, never a forced action.
"""
def route(current_frame, history_entries, valid_actions):
    actions = {str(a).upper() for a in valid_actions or []}
    mouse = bool(actions & {'MOUSE', 'ACTION6', 'CLICK'})
    directions = bool(actions & {'UP', 'DOWN', 'LEFT', 'RIGHT', 'ACTION1', 'ACTION2', 'ACTION3', 'ACTION4'})
    changes = []
    recent = (history_entries or [])[-9:]
    for before, after in zip(recent, recent[1:]):
        if before.frame.level != current_frame.level or after.frame.level != current_frame.level:
            continue
        a, b = before.frame.grid, after.frame.grid
        if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
            continue
        changes.append(sum(x != y for row1, row2 in zip(a, b) for x, y in zip(row1, row2)))
    # Tiny changes alone do not establish progress or mechanics. Keep the
    # threshold conservative and describe it as a hypothesis, not a classifier.
    if mouse and len(changes) >= 3 and all(0 < n <= 4 for n in changes[-3:]):
        return 'tiny_changes', ('Recent actions changed at most four pixels each. Cursor/HUD motion is a hypothesis, '
            'not evidence of puzzle progress. Inspect animation and compare predicted object changes; '
            'choose one probe that distinguishes cursor motion from a rule change before a long plan.')
    if mouse and not directions:
        return 'mouse_probe', ('Controls are clicks. If object-centre probes were ineffective, test one '
            'different spatial hypothesis, including empty regions between visible objects. Record '
            'the predicted change first; use the resulting observation to refine your coordinate model.')
    if directions and not mouse:
        return 'spatial', ('Directional controls are available. Infer displacement and blocked cells '
            'from observed transitions. If the goal and movement rule are supported, build a small '
            'coordinate graph, plan a route, and verify the next action before committing a long batch.')
    return 'mixed', ('Compare effects of the available control families with a small discriminating probe. '
        'Choose controls from observed effects; availability alone does not imply they are useful.')


def install(agent_class):
    original = agent_class._build_user_prompt
    def routed(self, *args, **kwargs):
        text = original(self, *args, **kwargs)
        frame = kwargs.get('current_frame')
        if frame is None:
            return text
        name, hint = route(frame, kwargs.get('history_entries', []), kwargs.get('valid_actions', []))
        self.__dict__.setdefault('_lab_routes', []).append(name)
        return text + '\nObservation-based strategy (experimental; revise when contradicted): ' + hint
    agent_class._build_user_prompt = routed
    original_python = agent_class._run_python_tool
    def python_tool(self, state_path, arguments):
        import ast
        import hashlib
        import json
        code = str(arguments.get('code', ''))
        try:
            tree = ast.parse(code)
            calls = {n.func.id if isinstance(n.func, ast.Name) else '<method>'
                     for n in ast.walk(tree) if isinstance(n, ast.Call)}
            # Deliberately narrow: never suppress action calls, unknown helpers,
            # method calls, imports, mutations, or model execution.
            pure = bool(calls) and calls <= {'print','range','len','min','max','sum','enumerate','zip','str','int','tuple','list'}
            pure = pure and not any(isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.AugAssign,ast.Delete)) for n in ast.walk(tree))
            state = json.loads(state_path.read_text(encoding='utf8'))['current_frame']
            key = hashlib.sha256(json.dumps([state,code],sort_keys=True).encode()).hexdigest()
            seen = self.__dict__.setdefault('_lab_inspections', {})
            seen[key] = seen.get(key, 0)+1
            if pure and seen[key] >= 3:
                self.__dict__.setdefault('_lab_routes',[]).append('repeat_inspection')
                arguments = {**arguments, 'code': 'print("OBSERVATION ROUTER: this identical inspection already ran twice on this unchanged observation. It adds no new evidence. State a testable hypothesis and choose one legal action that distinguishes it; inspect a different feature only if it can change that decision.")'}
        except (SyntaxError, KeyError, ValueError, OSError):
            pass
        return original_python(self, state_path, arguments)
    agent_class._run_python_tool = python_tool


def families(available):
    actions = set(available)
    mouse = 6 in actions
    directions = bool(actions & {1, 2, 3, 4})
    groups = ['all', 'mouse_only' if mouse and not directions else 'mixed' if mouse else 'keyboard_only']
    if 7 in actions:
        groups.append('undo_available')
    return groups
