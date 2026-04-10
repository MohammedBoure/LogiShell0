"""
inference_engine.py
-------------------
InferenceEngine — the core reasoning module of the Expert System.

Supports two inference modes defined in :class:`~models.ChainingMode`:

Forward Chaining (Data-driven)
    Starts from known facts and repeatedly fires applicable rules until
    no more new facts can be derived (fixed-point / closure).  The
    algorithm is *irrevocable* and *monotonic*: once a fact is added it
    is never retracted.  A Depth-First Search (DFS) agenda is used.

Backward Chaining (Goal-driven)
    Starts from a goal fact and recursively tries to prove it by finding
    rules whose conclusion matches the goal, then recursively attempting
    to prove each premise.  Implements *backtracking* so that alternative
    rules are tried when one branch fails.  Also DFS.

Conflict Resolution Strategy (applied in both modes)
    When multiple rules are applicable at the same decision point the
    engine selects the rule with the **highest number of premises**
    (most specific / highest specificity).  Ties are broken by choosing
    the rule with the **lexicographically smallest Rule ID**.
"""

from __future__ import annotations

from typing import FrozenSet, List, Optional, Set, Tuple

from .exceptions import GoalNotFoundError, InferenceError
from .knowledge_base import KnowledgeBase
from .models import (
    ChainingMode,
    InferenceResult,
    Rule,
    TraceEntry,
    TraceEventType,
)


# ---------------------------------------------------------------------------
# InferenceEngine
# ---------------------------------------------------------------------------

class InferenceEngine:
    """
    Propositional-logic inference engine supporting Forward and Backward
    chaining over a :class:`~knowledge_base.KnowledgeBase`.

    Parameters
    ----------
    kb : KnowledgeBase
        The knowledge base (rules + initial facts) to reason over.
    max_depth : int
        Maximum recursion depth for backward chaining (guards against
        infinite loops in cyclic rule graphs).  Default: 100.

    Examples
    --------
    >>> from expert_system import KnowledgeBase, InferenceEngine
    >>> kb = KnowledgeBase("kb.json")
    >>> engine = InferenceEngine(kb)
    >>> result = engine.forward_chain()
    >>> result.print_trace()
    """

    def __init__(self, kb: KnowledgeBase, max_depth: int = 100) -> None:
        self._kb: KnowledgeBase = kb
        self._max_depth: int = max_depth

    # ==================================================================
    # Public API
    # ==================================================================

    def forward_chain(
        self,
        extra_facts: Optional[Set[str]] = None,
    ) -> InferenceResult:
        """
        Run Forward Chaining (chaînage avant) to derive all reachable facts.

        The algorithm is irrevocable and monotonic: facts are never
        retracted.  A DFS agenda drives rule selection at each iteration.

        Parameters
        ----------
        extra_facts : set[str] | None
            Additional facts to seed the working memory beyond those
            declared in the knowledge base.  Useful for session-level
            overrides.

        Returns
        -------
        InferenceResult
            Contains the final working memory, fired rules, and the full
            reasoning trace.
        """
        # ── Initialise working memory ──────────────────────────────────
        working_memory: Set[str] = set(self._kb.initial_facts)
        if extra_facts:
            working_memory.update(extra_facts)

        initial_snapshot: FrozenSet[str] = frozenset(working_memory)
        trace: List[TraceEntry] = []
        fired_rules: List[str] = []
        step = 0

        def log(
            event: TraceEventType,
            message: str,
            rule_id: Optional[str] = None,
        ) -> None:
            nonlocal step
            step += 1
            trace.append(
                TraceEntry(
                    step=step,
                    event_type=event,
                    message=message,
                    rule_id=rule_id,
                    facts_snapshot=frozenset(working_memory),
                )
            )

        log(TraceEventType.INFO,
            f"Forward chaining started. "
            f"Working memory: {sorted(working_memory)}")

        # ── Main saturation loop ───────────────────────────────────────
        changed = True
        iteration = 0

        while changed:
            changed = False
            iteration += 1

            log(TraceEventType.INFO,
                f"--- Iteration {iteration}: "
                f"scanning for applicable rules ---")

            # Collect all currently applicable rules (premises ⊆ WM)
            applicable: List[Rule] = [
                r for r in self._kb.rules
                if r.conclusion not in working_memory
                   and r.is_applicable(frozenset(working_memory))
            ]

            if not applicable:
                log(TraceEventType.INFO,
                    "No applicable rules found — fixed point reached.")
                break

            # ── Conflict resolution ────────────────────────────────────
            selected = self._resolve_conflict(applicable)

            log(
                TraceEventType.CONFLICT_RESOLVED,
                f"{len(applicable)} applicable rule(s) found. "
                f"Selected [{selected.rule_id}] "
                f"(specificity={selected.specificity}, "
                f"candidates={[r.rule_id for r in applicable]}).",
                rule_id=selected.rule_id,
            )

            # Log skipped rules
            for skipped in applicable:
                if skipped.rule_id != selected.rule_id:
                    log(
                        TraceEventType.RULE_SKIPPED,
                        f"Rule {skipped} skipped (lower priority).",
                        rule_id=skipped.rule_id,
                    )

            # ── Fire the selected rule ─────────────────────────────────
            log(
                TraceEventType.RULE_EVALUATED,
                f"Evaluating rule {selected} — "
                f"premises {list(selected.premises)} all satisfied.",
                rule_id=selected.rule_id,
            )

            new_fact = selected.conclusion
            working_memory.add(new_fact)
            fired_rules.append(selected.rule_id)
            changed = True

            log(
                TraceEventType.RULE_FIRED,
                f"Rule [{selected.rule_id}] fired → "
                f"new fact derived: '{new_fact}'.",
                rule_id=selected.rule_id,
            )
            log(
                TraceEventType.FACT_ADDED,
                f"Fact '{new_fact}' added to working memory.",
                rule_id=selected.rule_id,
            )

        # ── Build result ───────────────────────────────────────────────
        final_wm: FrozenSet[str] = frozenset(working_memory)
        new_facts: FrozenSet[str] = final_wm - initial_snapshot
        success = len(new_facts) > 0

        log(
            TraceEventType.INFO,
            f"Forward chaining complete. "
            f"New facts derived: {sorted(new_facts)}. "
            f"Total rules fired: {len(fired_rules)}.",
        )

        return InferenceResult(
            mode=ChainingMode.FORWARD,
            success=success,
            goal=None,
            initial_facts=initial_snapshot,
            derived_facts=final_wm,
            new_facts=new_facts,
            fired_rules=fired_rules,
            trace=trace,
        )

    # ------------------------------------------------------------------

    def backward_chain(
        self,
        goal: str,
        extra_facts: Optional[Set[str]] = None,
    ) -> InferenceResult:
        """
        Run Backward Chaining (chaînage arrière) to prove *goal*.

        The algorithm performs DFS with backtracking: it attempts to
        prove the goal by finding a rule whose conclusion matches, then
        recursively proves each premise.  If a branch fails, it
        backtracks and tries the next candidate rule.

        Parameters
        ----------
        goal : str
            The fact-name to prove.
        extra_facts : set[str] | None
            Additional seed facts beyond those in the knowledge base.

        Returns
        -------
        InferenceResult
            success=True iff the goal was ultimately proven.

        Raises
        ------
        GoalNotFoundError
            If *goal* does not appear as any rule conclusion and is not
            an initial fact (i.e. it is entirely unknown to the KB).
        InferenceError
            If the maximum recursion depth is exceeded.
        """
        if not goal or not isinstance(goal, str):
            raise InferenceError("Goal must be a non-empty string.")

        # Quick sanity check — goal must be reachable in principle
        known_conclusions = {r.conclusion for r in self._kb.rules}
        all_known = known_conclusions | self._kb.initial_facts
        if goal not in all_known:
            raise GoalNotFoundError(
                f"Goal '{goal}' is neither an initial fact nor the "
                f"conclusion of any rule in the knowledge base."
            )

        # ── Initialise working memory ──────────────────────────────────
        working_memory: Set[str] = set(self._kb.initial_facts)
        if extra_facts:
            working_memory.update(extra_facts)

        initial_snapshot: FrozenSet[str] = frozenset(working_memory)
        trace: List[TraceEntry] = []
        fired_rules: List[str] = []
        step_counter = [0]  # mutable int in closure

        def log(
            event: TraceEventType,
            message: str,
            rule_id: Optional[str] = None,
        ) -> None:
            step_counter[0] += 1
            trace.append(
                TraceEntry(
                    step=step_counter[0],
                    event_type=event,
                    message=message,
                    rule_id=rule_id,
                    facts_snapshot=frozenset(working_memory),
                )
            )

        log(TraceEventType.INFO,
            f"Backward chaining started. "
            f"Goal: '{goal}'. "
            f"Working memory: {sorted(working_memory)}")

        # ── Recursive DFS prover ───────────────────────────────────────
        def prove(
            sub_goal: str,
            depth: int,
            visited_goals: Set[str],
        ) -> bool:
            """
            Attempt to prove *sub_goal* recursively.

            Parameters
            ----------
            sub_goal : str
                The fact to prove at this recursion level.
            depth : int
                Current recursion depth (checked against max_depth).
            visited_goals : set[str]
                Goals currently on the recursion stack (cycle detection).

            Returns
            -------
            bool
                True iff *sub_goal* was successfully proven.
            """
            indent = "  " * depth

            # ── Base case 1: already in WM ─────────────────────────────
            if sub_goal in working_memory:
                log(
                    TraceEventType.INFO,
                    f"{indent}Goal '{sub_goal}' already in working memory "
                    f"— trivially satisfied.",
                )
                return True

            # ── Depth guard ────────────────────────────────────────────
            if depth >= self._max_depth:
                raise InferenceError(
                    f"Maximum recursion depth ({self._max_depth}) exceeded "
                    f"while attempting to prove '{sub_goal}'. "
                    "Consider increasing max_depth or check for rule cycles."
                )

            # ── Cycle detection ────────────────────────────────────────
            if sub_goal in visited_goals:
                log(
                    TraceEventType.CYCLE_DETECTED,
                    f"{indent}Cycle detected: '{sub_goal}' is already being "
                    f"proved at a higher level — branch abandoned.",
                )
                return False

            # ── Find candidate rules ───────────────────────────────────
            candidates: List[Rule] = self._kb.rules_concluding(sub_goal)

            if not candidates:
                log(
                    TraceEventType.GOAL_FAILED,
                    f"{indent}No rules conclude '{sub_goal}' and it is not "
                    f"a known fact — goal unprovable.",
                )
                return False

            log(
                TraceEventType.INFO,
                f"{indent}Attempting to prove goal '{sub_goal}'. "
                f"Candidate rules: {[r.rule_id for r in candidates]}.",
            )

            # ── Try candidates in conflict-resolution order ────────────
            ordered_candidates = self._sort_by_priority(candidates)
            visited_goals = visited_goals | {sub_goal}  # immutable update

            for rule in ordered_candidates:
                log(
                    TraceEventType.RULE_EVALUATED,
                    f"{indent}Trying rule {rule} for goal '{sub_goal}'.",
                    rule_id=rule.rule_id,
                )

                branch_success = True
                premises_proven: List[str] = []

                for premise in rule.premises:
                    log(
                        TraceEventType.INFO,
                        f"{indent}  Sub-goal: prove '{premise}'.",
                        rule_id=rule.rule_id,
                    )
                    if not prove(premise, depth + 1, visited_goals):
                        log(
                            TraceEventType.BACKTRACK,
                            f"{indent}  Premise '{premise}' could not be "
                            f"proven — backtracking from rule "
                            f"[{rule.rule_id}].",
                            rule_id=rule.rule_id,
                        )
                        branch_success = False
                        break
                    premises_proven.append(premise)

                if branch_success:
                    # All premises proven — fire the rule
                    working_memory.add(sub_goal)
                    fired_rules.append(rule.rule_id)
                    log(
                        TraceEventType.RULE_FIRED,
                        f"{indent}Rule [{rule.rule_id}] fired — "
                        f"all premises {list(rule.premises)} satisfied.",
                        rule_id=rule.rule_id,
                    )
                    log(
                        TraceEventType.FACT_ADDED,
                        f"{indent}Fact '{sub_goal}' added to working memory.",
                        rule_id=rule.rule_id,
                    )
                    log(
                        TraceEventType.GOAL_ACHIEVED,
                        f"{indent}Goal '{sub_goal}' PROVED via "
                        f"rule [{rule.rule_id}].",
                        rule_id=rule.rule_id,
                    )
                    return True

            # ── All candidates exhausted without success ───────────────
            log(
                TraceEventType.GOAL_FAILED,
                f"{indent}All candidate rules for '{sub_goal}' exhausted "
                f"— goal FAILED.",
            )
            return False

        # ── Launch the prover ──────────────────────────────────────────
        proven = prove(goal, depth=0, visited_goals=set())

        final_wm: FrozenSet[str] = frozenset(working_memory)
        new_facts: FrozenSet[str] = final_wm - initial_snapshot

        if proven:
            log(
                TraceEventType.GOAL_ACHIEVED,
                f"Top-level goal '{goal}' has been PROVED. ✓",
            )
        else:
            log(
                TraceEventType.GOAL_FAILED,
                f"Top-level goal '{goal}' could NOT be proved. ✗",
            )

        return InferenceResult(
            mode=ChainingMode.BACKWARD,
            success=proven,
            goal=goal,
            initial_facts=initial_snapshot,
            derived_facts=final_wm,
            new_facts=new_facts,
            fired_rules=fired_rules,
            trace=trace,
        )

    # ==================================================================
    # Conflict resolution helpers
    # ==================================================================

    @staticmethod
    def _resolve_conflict(candidates: List[Rule]) -> Rule:
        """
        Select the highest-priority rule from a non-empty list.

        Priority order (descending):
        1. Highest ``specificity`` (= number of premises).
        2. Smallest ``rule_id`` (lexicographic) to break ties.

        Parameters
        ----------
        candidates : List[Rule]
            Non-empty list of applicable rules.

        Returns
        -------
        Rule
            The selected rule.
        """
        return InferenceEngine._sort_by_priority(candidates)[0]

    @staticmethod
    def _sort_by_priority(rules: List[Rule]) -> List[Rule]:
        """
        Sort rules by descending specificity, then ascending rule ID.

        Parameters
        ----------
        rules : List[Rule]
            Rules to sort.

        Returns
        -------
        List[Rule]
            Sorted copy (the original list is not mutated).
        """
        return sorted(
            rules,
            key=lambda r: (-r.specificity, r.rule_id),
        )
