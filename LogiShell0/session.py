"""
session.py
----------
Session — high-level façade that ties a :class:`~knowledge_base.KnowledgeBase`
and an :class:`~inference_engine.InferenceEngine` together into a single,
easy-to-use entry point.

A Session:
* Loads the KB from a JSON file.
* Accepts optional runtime facts that augment (but never replace) the
  KB's initial facts.
* Exposes ``run_forward()`` and ``run_backward(goal)`` convenience methods.
* Maintains a simple history of past :class:`~models.InferenceResult` objects
  so that a single session can be queried multiple times.
"""

from __future__ import annotations

from typing import List, Optional, Set

from .inference_engine import InferenceEngine
from .knowledge_base import KnowledgeBase
from .models import ChainingMode, InferenceResult


class Session:
    """
    A high-level expert-system session.

    Parameters
    ----------
    kb_filepath : str
        Path to the JSON knowledge-base file.
    extra_facts : set[str] | None
        Additional runtime facts to seed the working memory beyond those
        declared in the knowledge base.
    max_depth : int
        Maximum backward-chaining recursion depth (default 100).

    Attributes
    ----------
    kb : KnowledgeBase
        The loaded knowledge base (read-only once constructed).
    history : List[InferenceResult]
        All results produced during this session, in chronological order.

    Examples
    --------
    >>> session = Session("animal_kb.json", extra_facts={"has_feathers"})
    >>> result = session.run_forward()
    >>> result.print_trace()
    >>>
    >>> result2 = session.run_backward("is_bird")
    >>> result2.print_trace()
    """

    def __init__(
        self,
        kb_filepath: str,
        extra_facts: Optional[Set[str]] = None,
        max_depth: int = 100,
    ) -> None:
        self._kb: KnowledgeBase = KnowledgeBase(kb_filepath)
        self._engine: InferenceEngine = InferenceEngine(self._kb, max_depth=max_depth)
        self._extra_facts: Set[str] = set(extra_facts) if extra_facts else set()
        self._history: List[InferenceResult] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def kb(self) -> KnowledgeBase:
        """The loaded :class:`~knowledge_base.KnowledgeBase`."""
        return self._kb

    @property
    def history(self) -> List[InferenceResult]:
        """Ordered list of :class:`~models.InferenceResult` objects."""
        return list(self._history)  # defensive copy

    # ------------------------------------------------------------------
    # Inference convenience methods
    # ------------------------------------------------------------------

    def run_forward(self, extra_facts: Optional[Set[str]] = None) -> InferenceResult:
        """
        Execute Forward Chaining and record the result in *history*.

        Parameters
        ----------
        extra_facts : set[str] | None
            Additional call-specific facts merged with session-level extras.

        Returns
        -------
        InferenceResult
        """
        merged = self._extra_facts | (extra_facts or set())
        result = self._engine.forward_chain(extra_facts=merged or None)
        self._history.append(result)
        return result

    def run_backward(
        self,
        goal: str,
        extra_facts: Optional[Set[str]] = None,
    ) -> InferenceResult:
        """
        Execute Backward Chaining towards *goal* and record the result.

        Parameters
        ----------
        goal : str
            The fact-name to prove.
        extra_facts : set[str] | None
            Additional call-specific facts merged with session-level extras.

        Returns
        -------
        InferenceResult
        """
        merged = self._extra_facts | (extra_facts or set())
        result = self._engine.backward_chain(goal=goal, extra_facts=merged or None)
        self._history.append(result)
        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def print_kb_summary(self) -> None:
        """Print a formatted summary of the loaded knowledge base."""
        print(self._kb.summary())

    def print_history_summary(self) -> None:
        """Print a one-line summary for each past inference result."""
        if not self._history:
            print("No inference results yet.")
            return
        print(f"\n{'─'*60}")
        print(f"  Session history ({len(self._history)} run(s))")
        print(f"{'─'*60}")
        for i, r in enumerate(self._history, start=1):
            mode_tag = r.mode.name
            goal_tag = f"goal='{r.goal}'" if r.goal else "full-closure"
            outcome = "✓ SUCCESS" if r.success else "✗ FAILURE"
            print(
                f"  #{i}  [{mode_tag}]  {goal_tag}  "
                f"fired={r.fired_rules}  {outcome}"
            )
        print(f"{'─'*60}\n")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Session(kb={self._kb.filepath!r}, "
            f"extra_facts={self._extra_facts!r}, "
            f"runs={len(self._history)})"
        )
