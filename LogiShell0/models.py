"""
models.py
---------
Core data structures for the Propositional Logic Expert System.
All entities are modelled as immutable-friendly dataclasses with full
type annotations so that the rest of the library can rely on strict
contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ChainingMode(Enum):
    """Inference mode supported by the engine."""
    FORWARD = auto()
    BACKWARD = auto()


class TraceEventType(Enum):
    """Category of a single reasoning step recorded in the trace."""
    INFO = "INFO"
    RULE_EVALUATED = "RULE_EVALUATED"
    RULE_FIRED = "RULE_FIRED"
    RULE_SKIPPED = "RULE_SKIPPED"
    FACT_ADDED = "FACT_ADDED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"
    GOAL_ACHIEVED = "GOAL_ACHIEVED"
    GOAL_FAILED = "GOAL_FAILED"
    BACKTRACK = "BACKTRACK"
    CYCLE_DETECTED = "CYCLE_DETECTED"


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Rule:
    """
    Represents a Horn clause of the form:
        premise_1 ∧ premise_2 ∧ … ∧ premise_n  →  conclusion

    Attributes
    ----------
    rule_id : str
        Unique identifier (e.g. "R1").
    premises : tuple[str, ...]
        Immutable ordered collection of antecedent fact-names.
    conclusion : str
        The single consequent fact-name produced when all premises hold.
    description : str
        Human-readable label (optional, defaults to empty string).
    """

    rule_id: str
    premises: tuple  # tuple[str, ...]  — kept as plain `tuple` for Python 3.8 compat
    conclusion: str
    description: str = ""

    # ------------------------------------------------------------------
    # Derived properties (computed once thanks to frozen=True caching)
    # ------------------------------------------------------------------

    @property
    def specificity(self) -> int:
        """Return the number of premises (used in conflict resolution)."""
        return len(self.premises)

    def is_applicable(self, known_facts: frozenset) -> bool:
        """
        Check whether every premise is satisfied by the given fact-set.

        Parameters
        ----------
        known_facts : frozenset
            The set of currently established fact-names.

        Returns
        -------
        bool
            True if all premises are present in *known_facts*.
        """
        return all(p in known_facts for p in self.premises)

    def __str__(self) -> str:
        lhs = " ∧ ".join(self.premises) if self.premises else "∅"
        return f"[{self.rule_id}] {lhs} → {self.conclusion}"


# ---------------------------------------------------------------------------
# TraceEntry
# ---------------------------------------------------------------------------

@dataclass
class TraceEntry:
    """
    A single, atomic step recorded during the inference process.

    Attributes
    ----------
    step : int
        Sequential step counter (1-based).
    event_type : TraceEventType
        Category of the event.
    message : str
        Human-readable description of what happened.
    rule_id : Optional[str]
        Rule involved in this step (if applicable).
    facts_snapshot : Optional[frozenset]
        A snapshot of the working memory *after* this step.
    """

    step: int
    event_type: TraceEventType
    message: str
    rule_id: Optional[str] = None
    facts_snapshot: Optional[frozenset] = None

    def __str__(self) -> str:
        tag = f"[{self.event_type.value}]"
        rule_tag = f" (Rule: {self.rule_id})" if self.rule_id else ""
        return f"  Step {self.step:>3} {tag:<22}{rule_tag} — {self.message}"


# ---------------------------------------------------------------------------
# InferenceResult
# ---------------------------------------------------------------------------

@dataclass
class InferenceResult:
    """
    The complete output of one inference session.

    Attributes
    ----------
    mode : ChainingMode
        Which algorithm produced this result.
    success : bool
        • Forward  → True if at least one new fact was derived.
        • Backward → True if the goal was proven.
    goal : Optional[str]
        The goal fact (backward chaining only).
    initial_facts : frozenset
        Working memory before inference started.
    derived_facts : frozenset
        All facts present in working memory *after* inference.
    new_facts : frozenset
        Facts that were added during this session (derived − initial).
    fired_rules : List[str]
        Ordered list of rule IDs that were successfully fired.
    trace : List[TraceEntry]
        Full step-by-step reasoning trace.
    """

    mode: ChainingMode
    success: bool
    goal: Optional[str]
    initial_facts: frozenset
    derived_facts: frozenset
    new_facts: frozenset
    fired_rules: List[str]
    trace: List[TraceEntry]

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def print_trace(self) -> None:
        """Pretty-print the full reasoning trace to stdout."""
        width = 72
        title = f" {self.mode.name} CHAINING — REASONING TRACE "
        print("\n" + title.center(width, "═"))
        print(f"  Goal        : {self.goal or '(none — full closure)'}")
        print(f"  Initial WM  : {sorted(self.initial_facts)}")
        print(f"  Result      : {'✓ SUCCESS' if self.success else '✗ FAILURE'}")
        print("─" * width)
        for entry in self.trace:
            print(entry)
        print("─" * width)
        print(f"  Fired rules : {self.fired_rules}")
        print(f"  New facts   : {sorted(self.new_facts)}")
        print(f"  Final WM    : {sorted(self.derived_facts)}")
        print("═" * width + "\n")
