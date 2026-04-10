"""
knowledge_base.py
-----------------
Knowledge Base (KB) — responsible for loading, validating, and exposing
the rule set and initial facts that drive the inference engine.

Rules are read from a JSON file whose schema is:

.. code-block:: json

    {
        "facts": ["fact_a", "fact_b"],
        "rules": [
            {
                "id": "R1",
                "description": "Optional human label",
                "premises": ["fact_a", "fact_b"],
                "conclusion": "fact_c"
            }
        ]
    }

The KB deliberately performs no inference itself — it is a *passive*
repository that the InferenceEngine queries.
"""

from __future__ import annotations

import json
import os
from typing import Dict, FrozenSet, List, Optional, Tuple

from .exceptions import (
    FileNotFoundError,
    InvalidRuleFormatError,
    KnowledgeBaseError,
)
from .models import Rule


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """
    Loads and validates a propositional-logic knowledge base from a JSON
    file.  Exposes:

    * ``rules``         — ordered list of :class:`Rule` objects.
    * ``initial_facts`` — frozenset of fact-names given at load time.

    Parameters
    ----------
    filepath : str
        Path to the JSON knowledge-base file.

    Raises
    ------
    FileNotFoundError
        If *filepath* does not point to an existing file.
    KnowledgeBaseError
        If the JSON is malformed (not parseable).
    InvalidRuleFormatError
        If any rule entry violates the expected schema.
    """

    _REQUIRED_RULE_KEYS: Tuple[str, ...] = ("id", "premises", "conclusion")

    def __init__(self, filepath: str) -> None:
        self._filepath: str = filepath
        self._rules: List[Rule] = []
        self._initial_facts: FrozenSet[str] = frozenset()
        self._rule_index: Dict[str, Rule] = {}  # rule_id → Rule (fast lookup)

        self._load(filepath)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def rules(self) -> List[Rule]:
        """Return the ordered list of :class:`Rule` objects."""
        return list(self._rules)  # defensive copy

    @property
    def initial_facts(self) -> FrozenSet[str]:
        """Return the frozenset of facts declared in the JSON file."""
        return self._initial_facts

    @property
    def filepath(self) -> str:
        """Return the path of the loaded JSON file."""
        return self._filepath

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        Retrieve a rule by its ID.

        Parameters
        ----------
        rule_id : str
            The rule identifier (e.g. ``"R1"``).

        Returns
        -------
        Rule or None
            The matching rule, or *None* if not found.
        """
        return self._rule_index.get(rule_id)

    def rules_concluding(self, fact: str) -> List[Rule]:
        """
        Return all rules whose conclusion matches *fact*.

        Parameters
        ----------
        fact : str
            The fact-name to search for in rule conclusions.

        Returns
        -------
        List[Rule]
            Possibly-empty list of matching rules.
        """
        return [r for r in self._rules if r.conclusion == fact]

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"KnowledgeBase(file={os.path.basename(self._filepath)!r}, "
            f"rules={len(self._rules)}, "
            f"initial_facts={len(self._initial_facts)})"
        )

    def summary(self) -> str:
        """Return a human-readable summary of the KB contents."""
        lines = [
            f"Knowledge Base  : {self._filepath}",
            f"Initial facts   : {sorted(self._initial_facts)}",
            f"Total rules     : {len(self._rules)}",
        ]
        for rule in self._rules:
            desc = f"  ← {rule.description}" if rule.description else ""
            lines.append(f"  {rule}{desc}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal loading & validation
    # ------------------------------------------------------------------

    def _load(self, filepath: str) -> None:
        """
        Read, parse, and validate the JSON knowledge-base file.

        Parameters
        ----------
        filepath : str
            Filesystem path to the JSON file.
        """
        # --- 1. File existence -------------------------------------------
        if not os.path.isfile(filepath):
            raise FileNotFoundError(
                f"Knowledge base file not found: '{filepath}'"
            )

        # --- 2. JSON parsing ---------------------------------------------
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                raw: dict = json.load(fh)
        except json.JSONDecodeError as exc:
            raise KnowledgeBaseError(
                f"Malformed JSON in '{filepath}': {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise KnowledgeBaseError(
                f"Top-level JSON structure must be an object, got "
                f"{type(raw).__name__!r} in '{filepath}'"
            )

        # --- 3. Initial facts --------------------------------------------
        raw_facts = raw.get("facts", [])
        if not isinstance(raw_facts, list):
            raise KnowledgeBaseError(
                "'facts' must be a JSON array of strings."
            )
        invalid_facts = [f for f in raw_facts if not isinstance(f, str) or not f.strip()]
        if invalid_facts:
            raise KnowledgeBaseError(
                f"All facts must be non-empty strings. Problematic entries: {invalid_facts}"
            )
        self._initial_facts = frozenset(raw_facts)

        # --- 4. Rules ----------------------------------------------------
        raw_rules = raw.get("rules", [])
        if not isinstance(raw_rules, list):
            raise KnowledgeBaseError("'rules' must be a JSON array.")

        seen_ids: set = set()
        parsed_rules: List[Rule] = []

        for idx, entry in enumerate(raw_rules):
            rule = self._parse_rule(entry, idx, seen_ids)
            parsed_rules.append(rule)
            seen_ids.add(rule.rule_id)
            self._rule_index[rule.rule_id] = rule

        self._rules = parsed_rules

    def _parse_rule(self, entry: object, idx: int, seen_ids: set) -> Rule:
        """
        Validate and convert a raw JSON object into a :class:`Rule`.

        Parameters
        ----------
        entry : object
            Raw value from the JSON array.
        idx : int
            Zero-based position in the rules array (for error messages).
        seen_ids : set
            Set of rule IDs already parsed (duplicate detection).

        Returns
        -------
        Rule

        Raises
        ------
        InvalidRuleFormatError
            On any schema violation.
        """
        position = f"rules[{idx}]"

        if not isinstance(entry, dict):
            raise InvalidRuleFormatError(
                f"{position}: each rule must be a JSON object, "
                f"got {type(entry).__name__!r}."
            )

        # Required keys
        for key in self._REQUIRED_RULE_KEYS:
            if key not in entry:
                raise InvalidRuleFormatError(
                    f"{position}: missing required key '{key}'."
                )

        rule_id: str = entry["id"]
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise InvalidRuleFormatError(
                f"{position}: 'id' must be a non-empty string."
            )
        rule_id = rule_id.strip()

        if rule_id in seen_ids:
            raise InvalidRuleFormatError(
                f"{position}: duplicate rule ID '{rule_id}'."
            )

        premises_raw = entry["premises"]
        if not isinstance(premises_raw, list):
            raise InvalidRuleFormatError(
                f"{position} (id={rule_id!r}): 'premises' must be a list."
            )
        for p in premises_raw:
            if not isinstance(p, str) or not p.strip():
                raise InvalidRuleFormatError(
                    f"{position} (id={rule_id!r}): each premise must be a "
                    f"non-empty string, got {p!r}."
                )
        premises: tuple = tuple(p.strip() for p in premises_raw)

        conclusion: str = entry["conclusion"]
        if not isinstance(conclusion, str) or not conclusion.strip():
            raise InvalidRuleFormatError(
                f"{position} (id={rule_id!r}): 'conclusion' must be a "
                f"non-empty string."
            )
        conclusion = conclusion.strip()

        description: str = str(entry.get("description", "")).strip()

        return Rule(
            rule_id=rule_id,
            premises=premises,
            conclusion=conclusion,
            description=description,
        )
