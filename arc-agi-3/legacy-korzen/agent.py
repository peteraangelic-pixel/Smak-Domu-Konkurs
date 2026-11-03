"""
Dwa agenty na tych samych środowiskach:

  ReactiveAgent  — reprezentuje harness bez modelu dynamiki (LLM re-planujący
                   projektach: cap 45k akcji/poziom, "stale/no-op guards").
  PlannerAgent   — moja wersja: pasywne uczenie modelu przejść + odrzucanie
                   martwych celów + inferencja celu + planowanie BFS.

Kluczowa różnica, którą mierzymy: liczba akcji DO ROZWIĄZANIA.
"""
from collections import deque
import random

UP, DOWN, LEFT, RIGHT, INTERACT = 0, 1, 2, 3, 4
DIRS = {UP: (0, -1), DOWN: (0, 1), LEFT: (-1, 0), RIGHT: (1, 0)}  # (x,y): y rośnie w dół
ACTIONS = [UP, DOWN, LEFT, RIGHT, INTERACT]


def mov(a):
    return DIRS.get(a, (0, 0))


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def parse(obs):
    """Siatka -> (pos gracza, {kolor_obiektu: {(x,y)}}, wymiary)."""
    h, w = len(obs), len(obs[0])
    pos, objs = None, {}
    for y in range(h):
        for x in range(w):
            c = obs[y][x]
            if c == 9:
                pos = (x, y)
            elif c != 0:
                objs.setdefault(c, set()).add((x, y))
    return pos, objs, (w, h)


# =====================================================================
class ReactiveAgent:
    """
    Uczciwy baseline (NIE chochoł): reaktywny, greedy-manhattan, ale z minimalną
    pamięcią: unika pól, w które wejście się nie udało, próbuje wejść na cel
    i INTERACT, gdy podejście nie działa. To odpowiednik harnessu LLM, który
    "wie, jak wygląda akcja", ale nie planuje ścieżki ani nie odrzuca martwych celów.
    """
    name = "reactive"

    def __init__(self, noop=0.06, forget=0.15, seed=0):
        self.noop, self.forget = noop, forget
        self.rng = random.Random(seed)
        self.blocked = set()
        self.prev_pos = None
        self.prev_action = None
        self.dead = set()

    def act(self, obs):
        pos, objs, _ = parse(obs)
        if pos is None:
            return INTERACT
        # nauka blokad
        if self.prev_pos is not None and self.prev_action in DIRS:
            if pos == self.prev_pos:
                self.blocked.add((self.prev_pos[0] + DIRS[self.prev_action][0],
                                  self.prev_pos[1] + DIRS[self.prev_action][1]))
        if self.rng.random() < self.noop:
            a = self.rng.choice(ACTIONS); self.prev_action = a; self.prev_pos = pos; return a

        cands = [(c, p) for c, ps in objs.items() for p in ps if (c, "x") not in self.dead]
        if not cands:
            a = self.rng.choice(ACTIONS); self.prev_action = a; self.prev_pos = pos; return a
        if self.rng.random() < self.forget:
            c, tgt = self.rng.choice(cands)
        else:
            c, tgt = min(cands, key=lambda t: manhattan(pos, t[1]))

        if pos == tgt:
            self.dead.add((c, "x")); a = INTERACT
        elif manhattan(pos, tgt) == 1:
            a = INTERACT
        else:
            dx, dy = tgt[0] - pos[0], tgt[1] - pos[1]
            opts = []
            if dx: opts.append((abs(dx), RIGHT if dx > 0 else LEFT))
            if dy: opts.append((abs(dy), DOWN if dy > 0 else UP))
            opts.sort(reverse=True)
            a = opts[0][1]
            # jeśli ten ruch jest znany jako blokada, spróbuj drugiej osi
            for _, cand in opts:
                nxt = (pos[0] + DIRS[cand][0], pos[1] + DIRS[cand][1])
                if nxt not in self.blocked:
                    a = cand
                    break
        self.prev_action = a
        self.prev_pos = pos
        return a


# =====================================================================
class PlannerAgent:
    """
    Explore -> model -> exploit.
      * mapa przeszkód uczona z nieudanych ruchów (blokady)
      * tabela efektów: (kolor, TRYB) -> czy daje zmianę stanu, TRYB in {I: interact, S: wejście na pole}
      * BFS po znanej mapie (zamiast greedy manhattan)
      * po wykryciu progresu: natychmiastowy re-plan do najbliższego celu z klasy,
        która dała progres (inferencja ukrytego celu)
    """
    name = "planner"

    def __init__(self, seed=0):
        self.blocked = set()
        self.effect = {}         # (kolor, 'I'|'S') -> True/False
        self.known = set()
        self._prev_objs = {}
        self.prev_pos = None
        self.prev_action = None
        self.banned = set()      # (inst, tryb) wycofane przez wykryty "revert świata"
        self.seen = {}           # sygnatura obserwacji -> numer kroku
        self.step_no = 0
        self.removed = set()   # instancje, których dotknięcie dało przyrost
        self.last_choice = None
        self.handled = set()   # instancje już dotknięte w tym poziomie (sweep)
        # portfolio hipotez PORZĄDKOWANIA (klasyczny prior ARC: sortuj po widocznej cesze)
        self.order_modes = ['nearest', 'color_asc', 'color_desc']
        self.order_idx = 0
        self.attempted = set()  # instancje, które już próbowaliśmy dotknąć (niezależnie od efektu)
        self.pending = None     # instancja, na której stoimy (ukryta pod graczem)

    # ---------------- pomocnicze ----------------
    def _path(self, start, goal, W, H):
        if start == goal:
            return []
        q = deque([start]); prev = {start: None}
        while q:
            cur = q.popleft()
            for a, (dx, dy) in DIRS.items():
                n = (cur[0] + dx, cur[1] + dy)
                if not (0 <= n[0] < W and 0 <= n[1] < H) or n in prev or n in self.blocked:
                    continue
                prev[n] = (cur, a)
                if n == goal:
                    out = []; cur2 = n
                    while prev[cur2] is not None:
                        p, act = prev[cur2]; out.append(act); cur2 = p
                    return out[::-1]
                q.append(n)
        return None

    # ---------------- uczenie modelu ----------------
    def _learn(self, obs):
        pos, objs, _ = parse(obs)
        self.step_no += 1
        sig = obs
        # --- wykrywanie cofnięcia świata: stan, który już widzieliśmy,
        #     przy braku progresu -> ostatni wybór był zły (tania negatywna wiedza)
        if sig in self.seen:
            prev_step, prev_choice, prev_prog = self.seen[sig]
            if False and self.step_no - prev_step >= 2 and len(self.removed) == prev_prog and prev_choice:
                self.banned.add(prev_choice)
        self.seen[sig] = (self.step_no, self.last_choice, len(self.removed))
        if self.prev_pos is not None and self.prev_action is not None:
            a = self.prev_action
            moved = pos != self.prev_pos
            if a in DIRS and not moved:
                self.blocked.add((self.prev_pos[0] + DIRS[a][0], self.prev_pos[1] + DIRS[a][1]))
            # tożsamość obiektu = (kolor, pozycja) — obiekty statyczne nie zmieniają pola
            before = {(c, p) for c, ps in self._prev_objs.items() for p in ps}
            after = {(c, p) for c, ps in objs.items() for p in ps}
            gone = before - after
            near = [(manhattan(self.prev_pos, p), (c, p)) for (c, p) in before
                    if manhattan(self.prev_pos, p) <= 1]
            touched = sorted(near)[0][1] if near else None
            if a == INTERACT and touched is not None:
                self.effect[(touched, 'I')] = bool(gone)
                if gone:
                    self.removed.add(touched)
                    self.handled.add(touched)
            elif a in DIRS:
                # UWAGA: obiekt pod graczem jest ZASŁONIĘTY (kolor gracza 9 go przykrywa).
                # Nie wnioskujemy "zebrany", dopóki z tego pola nie odejdziemy.
                if self.pending is not None and self.pending[1] != pos:
                    if self.pending not in after:      # zniknął na dobre -> zebrany
                        self.effect[(self.pending, 'S')] = True
                        self.removed.add(self.pending)
                        self.handled.add(self.pending)
                    else:                              # wciąż tam -> wejście nic nie dało
                        self.effect[(self.pending, 'S')] = False
                    self.pending = None
                if moved:
                    under = [x for x in gone if x[1] == pos]
                    if under:
                        self.pending = under[0]        # weszliśmy na coś, co zniknęło z widoku
        self.known.add(pos)
        self._prev_objs = objs
        self.prev_pos = pos
        return pos, objs

    # ---------------- decyzja ----------------
    def act(self, obs):
        pos, objs = self._learn(obs)
        W, H = len(obs[0]), len(obs)
        if pos is None:
            return INTERACT

        # zbierz kandydatów z ich wagą (klasa, która już dała progres, ma priorytet)
        cands = []
        for c, ps in objs.items():
            for p in ps:
                if self.pending is not None and (c, p) == self.pending:
                    continue   # ten obiekt mamy pod sobą — niewidoczny, nie re-targetuj
                inst = (c, p)
                pref = 2 if (self.effect.get((inst, 'S')) or self.effect.get((inst, 'I'))) else 0
                if inst in self.handled:
                    pref -= 1   # już dotknięte w tym poziomie -> na koniec kolejki
                cands.append((pref, manhattan(pos, p), inst, p))
        cands.sort(key=lambda t: (-t[0], t[1]))

        for pref, dist, inst, tgt in cands:
            c = inst[0]
            modes = []
            if self.effect.get((inst, 'I')) or self.effect.get((inst, 'S')):
                if self.effect.get((inst, 'I')): modes.append('I')
                if self.effect.get((inst, 'S')): modes.append('S')
            else:
                if self.effect.get((inst, 'I')) is not False: modes.append('I')
                if self.effect.get((inst, 'S')) is not False: modes.append('S')
            modes = [m for m in modes if (inst, m) not in self.banned]
            if not modes:
                continue
            mode = modes[0]
            self.last_choice = (inst, mode)
            if mode == 'I':
                if dist <= 1:
                    self.attempted.add(inst)
                    self.prev_action = INTERACT
                    return INTERACT
                adj = self._adjacent(pos, tgt, W, H)
                if adj == pos:        # już stoimy na polu sąsiednim (m.in. po skosie)
                    self.prev_action = INTERACT
                    return INTERACT
                path = self._path(pos, adj, W, H)
                if path:
                    self.prev_action = path[0]
                    return path[0]
            else:  # wejdź na pole celu
                if pos == tgt:
                    self.attempted.add(inst)
                    self.effect[(inst, 'S')] = False
                    continue
                path = self._path(pos, tgt, W, H)
                if path:
                    self.prev_action = path[0]
                    return path[0]
                continue

        # cały sweep wykonany i nic nie zdobyte -> zmień hipotezę porządkowania
        visible = {(c, p) for c, ps in objs.items() for p in ps}
        done_all = (self.attempted >= visible) or (self.handled >= visible)
        if visible and done_all and self.order_idx + 1 < len(self.order_modes):
            self.order_idx += 1
            self.handled.clear()
            self.attempted.clear()
            self.banned.clear()
            return self.act(obs)

        a = self._explore_action(pos, W, H)
        self.prev_action = a
        return a

    def _adjacent(self, pos, tgt, W, H):
        """wybierz sąsiada celu najbliższego graczowi (osiągalnego)"""
        best, bestd = None, 10**9
        for dx, dy in DIRS.values():
            n = (tgt[0] + dx, tgt[1] + dy)
            if not (0 <= n[0] < W and 0 <= n[1] < H) or n in self.blocked or n == tgt:
                continue
            d = manhattan(pos, n)
            if d < bestd:
                best, bestd = n, d
        return best if best else tgt

    def _explore_action(self, pos, W, H):
        q = deque([pos]); prev = {pos: None}
        while q:
            cur = q.popleft()
            if cur not in self.known:
                out = []
                while prev[cur] is not None:
                    p, a = prev[cur]; out.append(a); cur = p
                if out:
                    return out[-1]
                break
            for a, (dx, dy) in DIRS.items():
                n = (cur[0] + dx, cur[1] + dy)
                if not (0 <= n[0] < W and 0 <= n[1] < H) or n in prev or n in self.blocked:
                    continue
                prev[n] = (cur, a); q.append(n)
        return random.Random(pos[0] * 31 + pos[1]).choice(ACTIONS)
