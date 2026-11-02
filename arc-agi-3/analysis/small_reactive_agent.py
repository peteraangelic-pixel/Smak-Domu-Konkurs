"""Bounded observation-only policy prototype. No training or engine access."""
import json
import time
import requests


class ReactivePolicy:
    def __init__(self, model='arc-small-reactive', endpoint='http://localhost:1234/api/v1/chat'):
        self.model, self.endpoint = model, endpoint
        self.previous = None
        self.errors = 0
        self.tactic = 0
        self.history = []

    def choose(self, grid, valid_actions, level):
        # The evaluator supplies pixels and public controls only.
        observed = []
        if self.previous and self.previous['level'] == level:
            old = self.previous['grid']
            observed = [[r, c, grid[r][c]] for r in range(len(grid))
                        for c in range(len(grid[r])) if old[r][c] != grid[r][c]]
            checks = self.previous['prediction']
            correct = all(grid[r][c] == color for r, c, color in checks)
            self.errors = self.errors + 1 if checks and not correct else 0
            if self.errors >= 2:
                self.tactic = (self.tactic + 1) % 3
                self.errors = 0
            self.history.append(dict(action=self.previous['action'],
                                     changed_cells=len(observed), prediction_correct=correct,
                                     prediction_checks=len(checks)))
        elif self.previous:
            self.history, self.errors, self.tactic = [], 0, 0
        tactics = ['discover controls with one discriminating experiment',
                   'discard contradicted rules and test a different causal explanation',
                   'execute one step toward a visible goal using observed rules']
        payload = dict(level=level, grid=[''.join(format(x, 'X') for x in row) for row in grid], valid_actions=valid_actions,
                       recent=self.history[-6:], tactic=tactics[self.tactic],
                       recent_changes=observed[:24])
        system = ('You control an unfamiliar grid game. Infer rules from observations. '
                  'Return ONE JSON object: {"action":"UP", "row":0,"col":0, '
                  '"predict":[[row,col,expected_color]],"reason":"brief causal hypothesis"}. '
                  'Use only a listed action. For MOUSE give pixel row/col; otherwise omit them. '
                  'Predict up to three cells after the action; these will be checked. '
                  'Do not invent success. Identical pixels may conceal state changes. '
                  'Grid characters are hexadecimal color codes 0-F; predicted colors are integers. '
                  'Avoid long descriptions. No code, no markdown.')
        start = time.perf_counter()
        response = requests.post(self.endpoint, json=dict(model=self.model,
            system_prompt=system, input=json.dumps(payload, separators=(',', ':')),
            reasoning='off', temperature=0.3, max_output_tokens=256), timeout=90)
        if not response.ok:
            self.last_response = dict(status=response.status_code, body=response.text)
        response.raise_for_status()
        raw = response.json()
        self.last_response = raw
        self.last_seconds = time.perf_counter() - start
        content = ''.join(part.get('content', '') for part in raw['output'] if part.get('type') == 'message')
        if content.strip().startswith('```json') and content.strip().endswith('```'):
            content = content.strip()[7:-3].strip()
        # Strict validation: malformed generations never cause an environment action.
        obj = json.loads(content)
        action = obj['action']
        if action not in valid_actions:
            raise ValueError('Model chose unavailable action: ' + str(action))
        choice = {'action': action}
        if action == 'MOUSE':
            row, col = obj['row'], obj['col']
            if type(row) is not int or type(col) is not int or not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
                raise ValueError('Invalid mouse coordinate')
            choice.update(row=row, col=col)
        prediction = obj.get('predict', [])
        if not isinstance(prediction, list) or len(prediction) > 3:
            raise ValueError('Invalid prediction count')
        for point in prediction:
            if not isinstance(point, list) or len(point) != 3 or not all(type(x) is int for x in point):
                raise ValueError('Invalid prediction')
            r, c, color = point
            if not (0 <= r < len(grid) and 0 <= c < len(grid[r]) and 0 <= color < 16):
                raise ValueError('Invalid prediction coordinate/color')
        record = dict(request=payload, response=raw, seconds=time.perf_counter() - start,
                      tactic=self.tactic, action=choice)
        self.previous = dict(grid=[list(row) for row in grid], level=level,
                             prediction=prediction, action=choice)
        return choice, record
