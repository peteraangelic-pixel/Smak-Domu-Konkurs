"""Experimental forward-only navigation from visible sprite translations.

No game identity, engine state, hidden baselines or precomputed paths.
Rectangle extraction may use the existing Rust FFI kernel.
"""
from collections import Counter, deque
import numpy as np
from template_transfer import rectangles


class MotionNavigator:
    DIRECTIONS = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}

    def __init__(self, extract_rectangles=rectangles, budget=160):
        self.extract = extract_rectangles
        self.budget = budget
        self.level = None
        self.previous = None
        self.action = None
        self.player = None
        self.pitch = None
        self.used = 0
        self.visits = Counter()
        self.blocked = set()
        self.floor = Counter()
        self.rejected = False

    def motion(self, before, after, action):
        dy, dx = self.DIRECTIONS[action]
        old = self.extract(before)
        new = set(self.extract(after))
        candidates = []
        for y0, y1, x0, x1, color in old:
            h, w = y1-y0, x1-x0
            if not (2 <= h <= 8 and 2 <= w <= 8 and .5 <= h/w <= 2):
                continue
            if y0 < 3 or y1 > before.shape[0]-3 or x0 < 2 or x1 > before.shape[1]-2:
                continue
            if (y0,y1,x0,x1,color) in new:
                continue
            for step in range(1, 9):
                yy, xx = y0+dy*step, x0+dx*step
                if (yy,yy+h,xx,xx+w,color) not in new:
                    continue
                # A translated rectangle must explain a local visible change.
                if self.player is not None and (y0,x0) != self.player:
                    continue
                candidates.append((h*w, yy, xx, step, y0, x0, h, w))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        if len(candidates)>1 and candidates[0][0] == candidates[1][0]:
            return None
        return candidates[0]

    def act(self, grid, available, level):
        a = np.asarray(grid, dtype=np.uint8)
        if 6 in available or not all(x in available for x in self.DIRECTIONS):
            return None
        if level != self.level:
            self.level = level
            self.previous = None
            self.player = None
            self.pitch = None
            self.action = None
            self.used = 0
            self.visits.clear(); self.blocked.clear(); self.floor.clear()
            self.rejected = False
        if self.rejected or self.used >= self.budget:
            return None
        if self.previous is not None:
            move = self.motion(self.previous, a, self.action)
            if move:
                _, y, x, step, oy, ox, h, w = move
                if self.pitch is not None and self.pitch != step:
                    self.rejected = True
                    return None
                self.pitch = step
                self.player = (y, x)
                exposed = a[oy:oy+h,ox:ox+w]
                vals, counts = np.unique(exposed, return_counts=True)
                self.floor[int(vals[counts.argmax()])] += 1
                self.visits[self.player] += 1
            elif self.player is not None:
                self.blocked.add((self.player,self.action))
        if self.player is None:
            # Bounded directional identification, then yield to the LLM.
            if self.used >= 4:
                self.rejected = True
                return None
            action = (1,4,2,3)[self.used]
        else:
            origin = self.player
            step = self.pitch
            floor = self.floor.most_common(1)[0][0]
            queue = deque([(origin, None)])
            seen = {origin}
            action = None
            while queue and len(seen) <= 4096:
                (y,x), first = queue.popleft()
                if first is not None and self.visits[(y,x)] == 0:
                    action = first
                    break
                for act,(dy,dx) in self.DIRECTIONS.items():
                    target = (y+dy*step,x+dx*step)
                    yy,xx = target
                    if target in seen or ((y,x),act) in self.blocked:
                        continue
                    if not (3 <= yy < a.shape[0]-3 and 2 <= xx < a.shape[1]-2):
                        continue
                    # Only extrapolate over terrain observed under the player.
                    patch = a[yy:min(yy+step,a.shape[0]),xx:min(xx+step,a.shape[1])]
                    object_tile = len(np.unique(patch)) >= 2
                    if int(a[yy,xx]) != floor and not object_tile and target != origin:
                        continue
                    seen.add(target)
                    queue.append((target,act if first is None else first))
            if action is None:
                actions = [act for act in self.DIRECTIONS if (origin,act) not in self.blocked]
                if not actions:
                    return None
                action = min(actions,key=lambda act:self.visits[(origin[0]+self.DIRECTIONS[act][0]*step,
                                                                 origin[1]+self.DIRECTIONS[act][1]*step)])
        self.previous = a.copy()
        self.action = action
        self.used += 1
        return (action, 0, 0)
