"""LLM-based policy for ARC-AGI-3.

Uses a local vLLM server (OpenAI-compatible API) to reason about game states.
Key design:
- The model outputs a PLAN with multiple actions when possible
- Actions are cached and executed without re-calling the model
- Anti-loop detection forces re-planning when stuck
- Context is managed to stay within the model's window
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
import urllib.error
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Sequence

from .grid_utils import (
    ARC_COLOR_CHARS,
    ARC_COLOR_LEGEND,
    format_grid_ascii,
    segment_grid,
    compact_segmentation_summary,
    grid_to_png_bytes,
)

# ---------------------------------------------------------------------------
# Action protocol
# ---------------------------------------------------------------------------
RESET = "RESET"
ACTION_NAMES = (RESET, *(f"ACTION{i}" for i in range(1, 8)))
COMPLEX_ACTION = "ACTION6"
DIRECTIONAL_ACTIONS = ("ACTION1", "ACTION2", "ACTION3", "ACTION4")
DIRECTION_NAMES = {
    "ACTION1": "UP", "ACTION2": "DOWN",
    "ACTION3": "LEFT", "ACTION4": "RIGHT",
}
MODEL_TO_ENGINE = {
    "UP": "ACTION1", "DOWN": "ACTION2",
    "LEFT": "ACTION3", "RIGHT": "ACTION4",
    "MOUSE": "ACTION6", "CLICK": "ACTION6",
}
ENGINE_TO_MODEL = {v: k for k, v in MODEL_TO_ENGINE.items()}
ENGINE_TO_MODEL.update(DIRECTION_NAMES)


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    base_url: str = ""
    model_id: str = ""
    api_key: str = "EMPTY"
    max_output_tokens: int = 2048
    temperature: float = 0.6
    top_p: float = 0.95
    top_k: int = 20
    timeout: float = 120.0
    context_window: int = 32768
    enable_thinking: bool = True
    multimodal: bool = False
    upscale: int = 4

    @classmethod
    def from_env(cls) -> LLMConfig:
        return cls(
            base_url=os.environ.get("LLM_BASE_URL", "http://127.0.0.1:1234/v1"),
            model_id=os.environ.get("LLM_MODEL_ID", ""),
            api_key=os.environ.get("LLM_API_KEY", "EMPTY"),
            max_output_tokens=int(os.environ.get("LLM_MAX_OUTPUT", "2048")),
            temperature=float(os.environ.get("LLM_TEMPERATURE", "0.6")),
            top_p=float(os.environ.get("LLM_TOP_P", "0.95")),
            top_k=int(os.environ.get("LLM_TOP_K", "20")),
            timeout=float(os.environ.get("LLM_TIMEOUT", "120")),
            context_window=int(os.environ.get("LLM_CONTEXT_WINDOW", "32768")),
            enable_thinking=os.environ.get("LLM_ENABLE_THINKING", "1").lower() in ("1", "true", "yes"),
            multimodal=os.environ.get("LLM_MULTIMODAL", "0").lower() in ("1", "true", "yes"),
            upscale=int(os.environ.get("LLM_UPSCALE", "4")),
        )


class LLMClient:
    """Minimal OpenAI-compatible chat completion client (no dependencies)."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.total_tokens = 0
        self.total_calls = 0
        self.total_time = 0.0
    
    def chat(self, messages: list[dict]) -> dict:
        """Call chat completions. Returns the message dict."""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        
        payload: dict[str, Any] = {
            "model": self.config.model_id,
            "messages": messages,
            "max_tokens": self.config.max_output_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "stream": False,
        }
        
        if self.config.enable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": True}
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )
        
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[LLM] Request failed after {time.time()-t0:.1f}s: {e}")
            return {"role": "assistant", "content": ""}
        finally:
            self.total_time += time.time() - t0
        
        self.total_calls += 1
        usage = result.get("usage", {})
        self.total_tokens += usage.get("total_tokens", 0)
        
        choices = result.get("choices", [])
        if choices:
            return choices[0].get("message", {"role": "assistant", "content": ""})
        return {"role": "assistant", "content": ""}


# ---------------------------------------------------------------------------
# System prompt (optimized for structured JSON output)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = f"""You are an expert puzzle solver playing a grid-based game. You see the game board as a 64×64 color grid and must figure out the mechanics through experimentation.

COLOR LEGEND: {ARC_COLOR_LEGEND}

HOW THE GAME WORKS:
- You control an avatar/agent on a colored grid
- You take actions to move, interact, or manipulate objects
- Levels are completed when you achieve the goal (often reaching a target, solving a puzzle, or clearing enemies)
- GAME_OVER means you died; the game auto-resets
- WIN means you beat the entire game

AVAILABLE ACTIONS (may vary per game):
- UP / DOWN / LEFT / RIGHT — move in a direction
- MOUSE(row=N, col=M) — click/interact at position (row, col)
- Other game-specific actions may appear in valid_actions

YOUR TASK EACH TURN:
1. Observe the current board state
2. Consider what changed since last turn (if history available)
3. Form/update a hypothesis about the game mechanics and goal
4. Choose the BEST next action

STRATEGIES:
- Start by exploring: move in different directions to understand the world
- Identify the player avatar (usually a distinct colored shape that moves)
- Identify obstacles, enemies, targets, and interactive objects
- For navigation puzzles, plan a path using BFS mentally
- If you die repeatedly, try a different approach
- Don't click on HUD elements (bars at edges that change each step)
- Objects are multi-tile connected components of the same color

IMPORTANT:
- Be decisive. Don't waste actions on indecision.
- If you've been stuck for 10+ actions, radically change strategy.
- Track what worked and what didn't (use "notes").
- Compact reasoning is fine, but always output a valid action.
- Deliberate LESS, act MORE: actions are cheap (~1.5x headroom before extra moves cost
  points), thinking tokens are the scarce resource. Max ~60 words per response.

FIELD GUIDE (patterns observed across ARC-AGI-3 training games — treat as priors, verify on the board):
- The win condition is almost always "ALL of something": all goal markers covered, all
  avatars on exits, all vessels filled, exactly one peg left. Partial progress gives NO
  signal — don't stop working because "most" of it is done.
- Dotted outlines, hollow contours, and small markers sharing the color of a movable
  object are usually the targets.
- A large area that no action seems to affect, yet looks like it should be editable, is
  almost always a PATTERN to copy, complete, or translate (≈40% of games).
- Some games check the result only after a CONFIRM action and give very few attempts:
  set the whole configuration up first, then confirm exactly once. Never confirm "to test".
- A counter that decreases every action is a step/lives LIMIT: it reaching 0 is a LOSS,
  never a win. Keep a margin; when it runs low, spend actions only on the safest known
  progress toward the goal.

LESSONS BETWEEN GAMES: at the start of a game you may see "Lessons from earlier
games in this run" — your own findings from sibling games (patterns common across
ARC games). Apply them as priors and verify against the new board.

GOAL PERSISTENCE: one game = one win condition for ALL its levels. Once you solve a
level, you almost certainly know the goal — record it in "notes". Later levels add
mechanics but do NOT change the goal class. If a level seems to contradict your goal,
re-check what actually changed on screen; do not invent extra objects to fit an old rule.

STUCK PROTOCOL: if many actions produce no level completion, stop re-trying variants of
the same idea. In "notes", list win-condition hypotheses you tested and FALSIFIED (✗),
form a different one, and run the cheapest experiment (1–2 actions) that distinguishes it.

OUTPUT FORMAT — end your response with one or more JSON action objects.
Single action (when uncertain or after an unexpected result):
```json
{{"action": "ACTION_NAME", "reasoning": "brief explanation"}}
```
Plan several actions at once (preferred for routine sequences, up to 8) —
they run in order until the next LLM call:
```json
{{"action": "UP", "reasoning": "step 1 of path"}}
{{"action": "LEFT", "reasoning": "step 2 of path"}}
```
or as one JSON array: `[{{"action": "UP"}}, {{"action": "LEFT"}}]`
For MOUSE actions: {{"action": "MOUSE", "row": 5, "col": 10, "reasoning": "..."}}
On the FIRST action object you may add a "notes" field — your compact memory for
this game: the current goal hypothesis, learned rules, falsified hypotheses (✗).
It is returned to you every turn; keep it under ~40 words, rewrite it when it changes:
```json
{{"action": "UP", "reasoning": "...", "notes": "GOAL: cover all dotted targets with the red cross. ✗ pushing boxes does nothing"}}
```
Do not output any other JSON objects.

BATCHING RULES:
- Plan a whole path or repetition (e.g. "move LEFT 5 times") as multiple
  action objects in ONE response — this saves thinking time for later.
- Stop the plan early (single action) if the next step depends on what a
  previous step reveals.
- The step counter shown in the HUD is the STEP LIMIT for the level, not a
  timer; nothing bad happens over time, only wasted steps. If it is running
  low, prioritize the safest known progress toward the goal.
- Experiment to learn mechanics, but prefer cheap experiments (one or two
  steps) over long deliberation. Always keep some budget to finish the level."""


# ---------------------------------------------------------------------------
# Frame info
# ---------------------------------------------------------------------------

@dataclass
class FrameInfo:
    grid: tuple[tuple[int, ...], ...]
    step: int
    level: int
    state_name: str
    levels_completed: int
    available_actions: list[str]
    
    @property
    def ascii(self) -> str:
        return format_grid_ascii(self.grid)
    
    @property
    def shape(self) -> tuple[int, int]:
        rows = len(self.grid)
        cols = max((len(r) for r in self.grid), default=0)
        return (rows, cols)
    
    def segmentation_summary(self) -> str:
        try:
            seg = segment_grid(self.grid)
            return compact_segmentation_summary(seg, max_nodes=15)
        except Exception:
            return "segmentation unavailable"


# ---------------------------------------------------------------------------
# State tracking for anti-loop
# ---------------------------------------------------------------------------

@dataclass
class StateTracker:
    """Track state transitions to detect loops."""
    
    state_signatures: list[str] = field(default_factory=list)
    action_history: list[str] = field(default_factory=list)
    state_action_counts: Counter = field(default_factory=Counter)
    game_over_count: int = 0
    total_actions: int = 0
    unique_states_seen: set = field(default_factory=set)
    
    # Recent window for loop detection
    _recent_sigs: list[str] = field(default_factory=list)
    _recent_actions: list[str] = field(default_factory=list)
    
    def record(self, state_sig: str, action: str, *,
               game_over: bool = False) -> None:
        self.state_signatures.append(state_sig)
        self.action_history.append(action)
        self.state_action_counts[(state_sig, action)] += 1
        self.total_actions += 1
        self.unique_states_seen.add(state_sig)
        
        self._recent_sigs.append(state_sig)
        if len(self._recent_sigs) > 12:
            self._recent_sigs = self._recent_sigs[-12:]
        
        self._recent_actions.append(action)
        if len(self._recent_actions) > 12:
            self._recent_actions = self._recent_actions[-12:]
        
        if game_over:
            self.game_over_count += 1
    
    def is_looped(self) -> bool:
        """Check if we're stuck repeating."""
        if len(self._recent_sigs) < 6:
            return False
        
        # Oscillation: same state appearing at positions 0,2,4
        last6 = self._recent_sigs[-6:]
        if last6[0] == last6[2] == last6[4] and last6[1] == last6[3] == last6[5]:
            return True
        
        # Same action repeated 6+ times
        if len(self._recent_actions) >= 6:
            last6a = self._recent_actions[-6:]
            if len(set(last6a)) == 1:
                return True
        
        # Same state repeated 4+ times
        if len(self._recent_sigs) >= 4:
            last4 = self._recent_sigs[-4:]
            if len(set(last4)) == 1:
                return True
        
        return False
    
    def repeated_in_state(self, state_sig: str, action: str) -> int:
        return self.state_action_counts.get((state_sig, action), 0)
    
    def reset(self) -> None:
        self.state_signatures.clear()
        self.action_history.clear()
        self.state_action_counts.clear()
        self.game_over_count = 0
        self.total_actions = 0
        self.unique_states_seen.clear()
        self._recent_sigs.clear()
        self._recent_actions.clear()


# ---------------------------------------------------------------------------
# Main LLM Policy
# ---------------------------------------------------------------------------

def _extract_action_objects(content: str) -> list[dict]:
    """Return every action dict found in `content`.

    Scans from each '{' or '[' with json.JSONDecoder.raw_decode, so nested
    braces (e.g. {"action": "UP", "reasoning": {...}}) and code fences are
    handled. Also unwraps JSON arrays of action objects, e.g.
    [{"action": "UP"}, {"action": "LEFT"}]. Invalid fragments are skipped.
    """
    decoder = json.JSONDecoder()
    found: list[dict] = []

    def next_pos(p: int) -> int:
        brace = content.find("{", p)
        bracket = content.find("[", p)
        if brace == -1:
            return bracket
        if bracket == -1:
            return brace
        return min(brace, bracket)

    pos = 0
    while True:
        start = next_pos(pos)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            pos = start + 1
            continue
        if isinstance(obj, dict) and "action" in obj:
            found.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and "action" in item:
                    found.append(item)
        pos = end
    return found


class LLMPolicy:
    """LLM-based policy with direct action output (no tool sandbox)."""
    
    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        self.client = LLMClient(self.config)
        self.tracker = StateTracker()
        
        # Conversation history for the current game
        self._messages: list[dict] = []
        self._initialized = False
        
        # Action cache: actions planned by LLM to execute without re-calling
        self._action_queue: list[dict] = []
        self._last_level = 0
        self._actions_since_last_llm = 0
        self._max_actions_per_plan = 15  # re-plan after this many actions
        
        # Game notes (agent's own compact memory, from the "notes" field) and
        # per-level action accounting for the stuck audit.
        self._game_notes: list[str] = []
        self._actions_on_level = 0
        self._last_audit_at = 0
        # Level whose "probe opening" was already queued (scripted opening:
        # try each safe direction once before spending LLM tokens).
        self._probe_level: int | None = None
        # No-op detection (SmartExplorer idea from the Pokemon branches):
        # attribute each executed action to whether the board changed.
        self._noop_recent: list[tuple[str, bool]] = []
        self._last_exec: str | None = None
        self._last_grid: tuple[tuple[int, ...], ...] | None = None
        # Run-level lessons harvested from finished games (kept across games).
        self._run_lessons: list[str] = []
        # Token accounting per level (stuck audit fires on tokens OR actions).
        self._level_start_tokens = 0
        self._audit_level_tokens = 0
        # Level whose structured notes are requested in the next user turn.
        self._pending_notes: int | None = None
    
    def reset_game(self) -> None:
        """Reset for a new game."""
        self._messages.clear()
        self._initialized = False
        self.tracker.reset()
        self._action_queue.clear()
        self._last_level = 0
        self._actions_since_last_llm = 0
        # Harvest this game's notes into run-level lessons first.
        for note in self._game_notes:
            if note not in self._run_lessons:
                self._run_lessons.append(note)
        if len(self._run_lessons) > 8:
            del self._run_lessons[:len(self._run_lessons) - 8]
        self._game_notes.clear()
        self._actions_on_level = 0
        self._last_audit_at = 0
        self._probe_level = None
        self._noop_recent.clear()
        self._last_exec = None
        self._last_grid = None
        self._level_start_tokens = self.total_tokens
        self._audit_level_tokens = 0
        self._pending_notes = None
    
    def choose_action(self, frame: FrameInfo) -> dict:
        """Choose an action for the current frame.
        
        Returns dict: {name: str, x: int|None, y: int|None, reasoning: dict}
        """
        state_sig = self._state_signature(frame)
        
        # Attribute the previous action's effect (no-op detection). Exact grid
        # equality: in games whose HUD changes every step the detector stays
        # silent (safe — no false positives), elsewhere it is reliable.
        if self._last_exec is not None and self._last_grid is not None:
            self._noop_recent.append((self._last_exec, frame.grid != self._last_grid))
            if len(self._noop_recent) > 10:
                del self._noop_recent[0]
        
        # Check for level change — re-plan immediately
        if frame.levels_completed != self._last_level:
            solved = frame.levels_completed > self._last_level
            self._last_level = frame.levels_completed
            self._action_queue.clear()
            self._actions_since_last_llm = 0
            self._actions_on_level = 0
            self._last_audit_at = 0
            self._level_start_tokens = self.total_tokens
            self._audit_level_tokens = 0
            # Notes are kept: one game = one win condition across levels.
            if solved:
                # levels_completed = liczba rozwiązanych; ostatnio rozwiązany = -1
                self._pending_notes = max(0, frame.levels_completed - 1)
        
        # Scripted probe opening (tape-opening idea from PTCG replay analysis):
        # at the start of each level, execute each safe direction action once,
        # before any LLM call. Movement is cheap and the resulting state changes
        # are the raw material for mechanic hypotheses. Confirm-type actions are
        # NEVER probed blindly (some games check results only on confirm).
        if self._probe_level != frame.levels_completed:
            self._probe_level = frame.levels_completed
            self._action_queue.extend(self._probe_actions(frame))
            # Add level change notification to history
            if self._messages:
                self._messages.append({
                    "role": "user",
                    "content": f"[LEVEL COMPLETED! Now on level {frame.levels_completed + 1}. Re-assess the new board.]"
                })
        
        # Check for loop
        if self.tracker.is_looped():
            self._action_queue.clear()
            return self._anti_loop_action(frame)
        
        # Try to use cached action
        if self._action_queue and self._actions_since_last_llm < self._max_actions_per_plan:
            action = self._action_queue.pop(0)
            self._actions_since_last_llm += 1
            self._actions_on_level += 1
            self.tracker.record(state_sig, action.get("name", RESET))
            self._mark_executed(frame, action.get("name", RESET))
            return action
        
        # Need to call LLM
        self._action_queue.clear()
        self._actions_since_last_llm = 0
        
        # Build user turn
        user_content = self._build_user_turn(frame)
        
        if not self._messages:
            self._messages.append({"role": "system", "content": SYSTEM_PROMPT})
        
        self._messages.append({"role": "user", "content": user_content})
        
        # Trim context if too long
        self._trim_context()
        
        # Call LLM
        response = self.client.chat(self._messages)
        content = response.get("content", "") or ""
        
        # Add assistant response to history
        self._messages.append({"role": "assistant", "content": content})
        
        # Parse action(s) from response
        actions = self._parse_response(content, frame)
        self._absorb_notes(actions)
        
        if not actions:
            # Fallback: try different directions
            action = self._fallback_action(frame)
            self.tracker.record(state_sig, action.get("name", RESET))
            self._actions_on_level += 1
            self._mark_executed(frame, action.get("name", RESET))
            return action
        
        # First action is immediate, rest go to queue
        immediate = actions[0]
        self._action_queue = actions[1:]
        self._actions_since_last_llm = 1
        self._actions_on_level += 1
        
        self.tracker.record(state_sig, immediate.get("name", RESET))
        self._mark_executed(frame, immediate.get("name", RESET))
        return immediate
    
    def _mark_executed(self, frame: FrameInfo, name: str) -> None:
        """Remember the executed action and the board it acted on."""
        self._last_exec = name
        self._last_grid = frame.grid
    
    @staticmethod
    def _probe_actions(frame: FrameInfo) -> list[dict]:
        """Safe scripted opening for a fresh level: each direction once.

        Only movement actions (ACTION1–ACTION4) are probed — never RESET and
        never ACTION5/ACTION6-style actions, because some games check the
        result only on a confirm/click action and give very few attempts.
        """
        probes = []
        for engine in ("ACTION1", "ACTION2", "ACTION3", "ACTION4"):
            if engine in frame.available_actions:
                probes.append({"name": engine, "reasoning": {"probe": True}})
        return probes
    
    def _absorb_notes(self, actions: list[dict]) -> None:
        """Capture the "notes" field from parsed actions into game memory."""
        for action in actions:
            note = action.pop("notes", None)
            if note:
                text = str(note).strip()
                if text and (not self._game_notes or self._game_notes[-1] != text):
                    self._game_notes.append(text)
                    if len(self._game_notes) > 4:
                        del self._game_notes[0]
    
    def _stuck_audit(self) -> str | None:
        """Stuck audit on the same level: fires on actions (>=40, then every 15)
        OR on tokens spent this level (>=50k, then every 20k)."""
        fired = False
        level_tokens = self.total_tokens - self._level_start_tokens
        if self._actions_on_level >= 40 and self._actions_on_level - self._last_audit_at >= 15:
            fired = True
        if level_tokens >= 50000 and level_tokens - self._audit_level_tokens >= 20000:
            fired = True
        if not fired:
            return None
        self._last_audit_at = self._actions_on_level
        self._audit_level_tokens = level_tokens
        return (
            f"⚠ STRATEGY AUDIT: {self._actions_on_level} actions and "
            f"~{level_tokens // 1000}k tokens spent on this level without solving it. "
            "Before more actions, answer in at most 6 short lines: (1) which goal/"
            "mechanic hypotheses you tested and which are FALSIFIED (mark ✗ in notes), "
            "(2) which board elements, colors or valid actions you have NOT yet tried, "
            "(3) whether the goal differs from your assumption (one game = one win "
            "condition — but later levels add mechanics). Then run the single cheapest "
            "1–2 action experiment that best distinguishes the remaining hypotheses."
        )
    
    def _state_signature(self, frame: FrameInfo) -> str:
        """Compact state signature for loop detection."""
        # Downsample: take every 4th row, every 4th col
        rows = frame.grid
        sampled = []
        for r in range(0, len(rows), 4):
            row_sample = []
            for c in range(0, len(rows[r]), 4):
                row_sample.append(rows[r][c])
            sampled.append(tuple(row_sample))
        payload = f"{frame.level}:{frame.state_name}:{sampled}".encode()
        return hashlib.md5(payload).hexdigest()[:12]
    
    def _build_user_turn(self, frame: FrameInfo) -> str:
        """Build user message with current game state."""
        parts = []
        
        # Status line
        parts.append(f"=== Turn {self.tracker.total_actions + 1} | "
                    f"Level {frame.level} | Step {frame.step} | "
                    f"State: {frame.state_name} | "
                    f"Levels done: {frame.levels_completed} ===")
        
        # One-time structured notes request after solving a level
        if self._pending_notes is not None:
            n = self._pending_notes
            self._pending_notes = None
            parts.append(
                f"First, write one short paragraph starting with \u201cLEVEL {n} NOTES:\u201d "
                "stating the mechanics you verified, the win condition, and the action "
                "pattern that solved it (max 4 short sentences). Then give the usual "
                "JSON action(s) for the new level.")
        
        # Available actions
        model_actions = []
        for a in frame.available_actions:
            model_name = ENGINE_TO_MODEL.get(a, a)
            model_actions.append(model_name)
        parts.append(f"Valid actions: {', '.join(model_actions)}")
        
        # Stats
        if self.tracker.total_actions > 0:
            parts.append(f"Stats: {self.tracker.total_actions} actions taken, "
                        f"{len(self.tracker.unique_states_seen)} unique states seen, "
                        f"{self.tracker.game_over_count} deaths")
        
        # Board (compact)
        rows, cols = frame.shape
        if rows <= 40 and cols <= 40:
            parts.append(f"\nBoard ({rows}×{cols}):")
            # Add row numbers every 10
            ascii_board = frame.ascii
            parts.append(ascii_board)
        else:
            parts.append(f"\nBoard is {rows}×{cols} (large — key objects below)")
        
        # Segmentation
        seg = frame.segmentation_summary()
        parts.append(f"\nObjects detected:\n{seg}")
        
        # Recent history (last 5 actions)
        if self.tracker.action_history:
            recent = self.tracker.action_history[-5:]
            parts.append(f"\nRecent actions: {' → '.join(ENGINE_TO_MODEL.get(a, a) for a in recent)}")
        
        # Agent's own game notes (from earlier "notes" fields)
        if self._game_notes:
            parts.append("\nYour game notes:")
            for note in self._game_notes:
                parts.append(f"- {note}")
        
        # Run-level lessons: injected on the first LLM turn of each game
        if self._run_lessons and not self.tracker.action_history:
            parts.append("\nLessons from earlier games in this run:")
            for lesson in self._run_lessons:
                parts.append(f"- {lesson}")
        
        # No-op feedback (only when there is something worth saying)
        noop_total = len(self._noop_recent)
        if noop_total >= 6:
            noops = [name for name, changed in self._noop_recent if not changed]
            if len(noops) >= 3:
                detail = ", ".join(f"{n}×{c}" for n, c in Counter(noops).most_common(3))
                parts.append(
                    f"\nNo-op check: {len(noops)}/{noop_total} recent actions did NOT "
                    f"change the board ({detail}). Such actions likely cannot help in "
                    "this state — don't repeat them expecting a different result.")
        
        # Actions on this level + periodic stuck audit
        parts.append(f"\nActions on this level: {self._actions_on_level}")
        audit = self._stuck_audit()
        if audit:
            parts.append(f"\n{audit}")
        
        # Anti-loop warning
        if self.tracker.is_looped():
            parts.append("\n⚠️ WARNING: You appear to be stuck in a loop! "
                        "Try a COMPLETELY different approach.")
        
        return "\n".join(parts)
    
    def _parse_response(self, content: str, frame: FrameInfo) -> list[dict]:
        """Parse action(s) from LLM response."""
        actions = []
        
        # Look for JSON objects with an "action" key (also with nested objects,
        # e.g. {"action": "UP", "reasoning": {...}}; the old non-greedy regex
        # cut those at the first "}" and silently dropped the action).
        for parsed in _extract_action_objects(content):
            action = self._normalize_action(parsed, frame)
            if action:
                actions.append(action)
        
        # If no JSON found, try to parse from text
        if not actions:
            action = self._parse_text_action(content, frame)
            if action:
                actions.append(action)
        
        return actions
    
    def _normalize_action(self, parsed: dict, frame: FrameInfo) -> dict | None:
        """Normalize a parsed action dict to our format."""
        action_name = str(parsed.get("action", "")).upper().strip()
        if not action_name:
            return None
        
        # Map friendly names to engine names
        engine_name = MODEL_TO_ENGINE.get(action_name, action_name)
        
        # Validate against available actions
        valid = set(frame.available_actions) | {RESET}
        if engine_name not in valid:
            # Try to find closest match
            for avail in frame.available_actions:
                if avail in action_name or action_name in avail:
                    engine_name = avail
                    break
            else:
                # Check if it's a direction in different format
                if action_name in ("UP", "DOWN", "LEFT", "RIGHT"):
                    engine_name = MODEL_TO_ENGINE.get(action_name, "RESET")
                else:
                    return None
        
        result = {"name": engine_name, "reasoning": {}}
        
        if engine_name == COMPLEX_ACTION:
            # MOUSE/CLICK needs coordinates
            row = parsed.get("row", parsed.get("y", 0))
            col = parsed.get("col", parsed.get("x", 0))
            result["x"] = int(col)
            result["y"] = int(row)
        
        reasoning = parsed.get("reasoning", "")
        if reasoning:
            result["reasoning"]["llm"] = str(reasoning)[:200]
        
        return result
    
    def _parse_text_action(self, text: str, frame: FrameInfo) -> dict | None:
        """Try to parse action from free text."""
        text_upper = text.upper()
        
        # Look for action patterns
        for pattern, engine_name in [
            (r'\bUP\b', 'ACTION1'), (r'\bDOWN\b', 'ACTION2'),
            (r'\bLEFT\b', 'ACTION3'), (r'\bRIGHT\b', 'ACTION4'),
            (r'\bRESET\b', 'RESET'),
        ]:
            if re.search(pattern, text_upper):
                if engine_name in frame.available_actions or engine_name == RESET:
                    return {"name": engine_name, "reasoning": {"parsed_from_text": True}}
        
        # Look for MOUSE/click patterns with coordinates
        mouse_match = re.search(r'MOUSE\s*\(\s*row\s*=\s*(\d+)\s*,\s*col\s*=\s*(\d+)\s*\)', text, re.I)
        if not mouse_match:
            mouse_match = re.search(r'CLICK\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', text, re.I)
        if mouse_match and COMPLEX_ACTION in frame.available_actions:
            return {
                "name": COMPLEX_ACTION,
                "x": int(mouse_match.group(2)),
                "y": int(mouse_match.group(1)),
                "reasoning": {"parsed_from_text": True},
            }
        
        return None
    
    def _anti_loop_action(self, frame: FrameInfo) -> dict:
        """Generate an action to break out of a loop."""
        import random
        
        available = [a for a in frame.available_actions if a != RESET]
        
        # Strategy 1: Reset
        if self.tracker.game_over_count < 3:
            return {"name": RESET, "reasoning": {"anti_loop": "reset"}}
        
        # Strategy 2: Try all different actions
        tried_recent = set(self.tracker._recent_actions[-6:])
        untried = [a for a in available if a not in tried_recent]
        
        if untried:
            choice = random.choice(untried)
            return {"name": choice, "reasoning": {"anti_loop": "try_untried"}}
        
        # Strategy 3: Random from available
        if available:
            choice = random.choice(available)
            return {"name": choice, "reasoning": {"anti_loop": "random"}}
        
        return {"name": RESET, "reasoning": {"anti_loop": "no_actions"}}
    
    def _fallback_action(self, frame: FrameInfo) -> dict:
        """Fallback when LLM fails to produce an action."""
        import random
        
        available = [a for a in frame.available_actions if a != RESET]
        if available:
            # Prefer directional actions
            dirs = [a for a in available if a in DIRECTIONAL_ACTIONS]
            if dirs:
                choice = random.choice(dirs)
            else:
                choice = random.choice(available)
            return {"name": choice, "reasoning": {"fallback": True}}
        
        return {"name": RESET, "reasoning": {"fallback": True}}
    
    def _trim_context(self) -> None:
        """Keep conversation within context window."""
        max_turns = 20  # system + last N user/assistant pairs
        if len(self._messages) > max_turns:
            system = [m for m in self._messages if m["role"] == "system"]
            others = [m for m in self._messages if m["role"] != "system"]
            # Keep last N turns
            self._messages = system + others[-(max_turns - len(system)):]
    
    def record_result(self, result: dict) -> None:
        """Record action result for context (optional)."""
        pass  # Results are incorporated via frame changes
    
    @property
    def total_tokens(self) -> int:
        return self.client.total_tokens
    
    @property
    def total_calls(self) -> int:
        return self.client.total_calls
