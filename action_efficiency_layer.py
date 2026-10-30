"""
ARC-AGI-3 — warstwa "action efficiency" do wpięcia w harness Duck/Franzen.

NIE jest to nowy agent. To trzy tanie mechanizmy, które zmniejszają liczbę
AKCJI do ukończenia poziomu (a RHAE = (human_actions/ai_actions)^2, cap 1.15):

  1. PlanCache        — powtarzalne plany wielokrokowe są odtwarzane, nie re-planowane
  2. ConvergedGuard   — stan, do którego wracamy bez progresu, jest banowany (tania negatywna wiedza)
  3. BudgetLedger     — budżet akcji per gra, twarde odcięcie "przedwczesnej eskalacji"

Zmierzone w arc3_lab: RHAE 3.80 -> 40.06 na 4 mikro-środowiskach
(ale uwaga: na jednym z nich warstwa PRZEGRYWA z prymitywnym baseline — patrz RAPORT.md §5).

Integracja z harnessem: patrz docstring `HarnessHook`.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict


# --------------------------------------------------------------------------
def state_key(obs) -> bytes:
    """Stabilny klucz stanu (hash pełnej obserwacji)."""
    if isinstance(obs, (bytes, bytearray)):
        return bytes(obs)
    return hashlib.blake2b(repr(obs).encode(), digest_size=16).digest()


# --------------------------------------------------------------------------
class PlanCache:
    """
    Jeśli z danego stanu prowadzi sprawdzony ciąg akcji, odtwórz go bez
    pytania modelu. Oszczędza przede wszystkim akcje decyzyjne i tokeny.

    Zysk: liczba "re-planowań" ~ liczba poziomów, nie liczba kroków.
    """

    def __init__(self, max_len=64):
        self.map = {}
        self.max_len = max_len
        self.hits = 0
        self.misses = 0

    def get(self, obs):
        k = state_key(obs)
        seq = self.map.get(k)
        if seq:
            self.hits += 1
            return list(seq)
        self.misses += 1
        return None

    def put(self, obs, actions):
        if not actions or len(actions) > self.max_len:
            return
        self.map[state_key(obs)] = list(actions)

    def learn_from_episode(self, frames, actions):
        """Z jednego epizodu: każde (stan -> reszta ciągu) staje się planem."""
        assert len(frames) == len(actions), "frames/actions muszą mieć równą długość"
        for i in range(len(actions)):
            rest = actions[i:]
            if 1 <= len(rest) <= self.max_len:
                # ucz tylko z krok>0: stan początkowy ma już pełny plan
                self.map.setdefault(state_key(frames[i]), rest)


# --------------------------------------------------------------------------
class ConvergedGuard:
    """
    Wykrywa "osiągnięty stan ustalony": obserwacja, którą już widzieliśmy
    N razy, przy braku postępu (poziom się nie zmienił, score nie rósł).
    Wtedy nie powtarzamy — banujemy ostatnią decyzję i wymuszamy inny wybór.

    W harnessie LLM to bezpośredni zamiennik "anti-loop heuristics"
    (oscillation / repeated action / stale state), ale oparty na hashach stanu,
    nie na oknie ostatnich k akcji — łapie pętle DŁUŻSZE niż okno.
    """

    def __init__(self, repeat_threshold=3, ban_ttl=40):
        self.seen = defaultdict(int)
        self.last_choice = None
        self.banned = {}          # choice -> licznik kroków ważności
        self.t = 0
        self.repeat_threshold = repeat_threshold
        self.ban_ttl = ban_ttl
        self.triggered = 0
        self._last_progress = None

    def observe(self, obs, progress_token):
        """
        progress_token: cokolwiek, co rośnie przy postępie (numer poziomu,
        liczba ukończonych celów, score). Musi być tanie.
        """
        self.t += 1
        for c in list(self.banned):
            self.banned[c] -= 1
            if self.banned[c] <= 0:
                del self.banned[c]
        # progres unieważnia licznik pętli: nowy poziom = nowa gra
        if self._last_progress is not None and progress_token != self._last_progress:
            self.seen.clear()
            self.banned.clear()
        self._last_progress = progress_token
        k = (state_key(obs), progress_token)
        self.seen[k] += 1
        if self.seen[k] >= self.repeat_threshold and self.last_choice is not None:
            self.banned[self.last_choice] = self.ban_ttl
            self.seen[k] = 0
            self.triggered += 1
            return True
        return False

    def filter(self, candidates):
        out = [c for c in candidates if c not in self.banned]
        return out if out else list(candidates)

    def commit(self, choice):
        self.last_choice = choice


# --------------------------------------------------------------------------
class BudgetLedger:
    """
    Budżet akcji per gra. Bez tego typowy błąd (udokumentowany w repo
    użytkownika): "przedwczesna eskalacja" — model zużywa akcje na poziomy,
    których i tak nie ukończy, odbierając budżet grom, które ukończy.

    Polityka: akcje idą najpierw tam, gdzie oczekiwany zysk jest najwyższy:
        priority = (levels_completed * w1) / (actions_used + w2)
    """

    def __init__(self, total_actions, w1=1.0, w2=200.0, min_share=0.02):
        self.total = total_actions
        self.used = defaultdict(int)
        self.levels = defaultdict(int)
        self.w1, self.w2, self.min_share = w1, w2, min_share

    def spend(self, game):
        self.used[game] += 1

    def completed(self, game):
        self.levels[game] += 1

    def priority(self, game):
        return (self.levels[game] * self.w1) / (self.used[game] + self.w2)

    def pick_game(self, active):
        """Wybierz grę do obsłużenia teraz (albo None, gdy budżet wyczerpany)."""
        spent = sum(self.used.values())
        if spent >= self.total:
            return None
        active = [g for g in active if self.used[g] < self.total * 0.25]
        if not active:
            return None
        return max(active, key=self.priority)

    def report(self):
        return {
            g: {"actions": self.used[g], "levels": self.levels[g]}
            for g in self.used
        }


# --------------------------------------------------------------------------
class HarnessHook:
    """
    Jak to wpiąć w istniejący notebook (Duck / Franzen M2), bez przepisywania agenta:

        hook = HarnessHook(total_actions=..., n_games=...)
        while time_left():
            g = hook.ledger.pick_game(active_games)   # 3. budżet
            obs = gateway.observe(g)

            plan = hook.cache.get(obs)                # 1. plan z cache
            if plan:
                a = plan[0]
            else:
                if hook.guard.observe(obs, gateway.level(g)):   # 2. stan ustalony
                    model_actions = hook.guard.filter(model_candidates(...))
                a = choose(model_actions(...))

            gateway.act(g, a)
            hook.ledger.spend(g)
            if gateway.level(g) != level_before:
                hook.ledger.completed(g)
                hook.cache.put(obs, tail_of_actions)
            hook.guard.commit(a)

    Kolejność ma znaczenie: cache PRZED modelem (oszczędza tokeny i akcje),
    guard PO modelu (filtruje jego wybór), ledger NAD wszystkim (decyduje,
    której grze w ogóle warto poświęcić czas GPU).
    """

    def __init__(self, total_actions, repeat_threshold=3):
        self.cache = PlanCache()
        self.guard = ConvergedGuard(repeat_threshold=repeat_threshold)
        self.ledger = BudgetLedger(total_actions)
