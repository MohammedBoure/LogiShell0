#!/usr/bin/env python3
"""
example_usage.py
----------------
Demonstrates the Expert System library with both Forward and Backward
chaining, using the animal-classification knowledge base.

Run from the repo root:
    python example_usage.py
"""

from __future__ import annotations

import sys
import os

# ── Allow running from the repo root without installing the package ──
sys.path.insert(0, os.path.dirname(__file__))

from LogiShell0 import (
    Session,
    KnowledgeBase,
    InferenceEngine,
    ChainingMode,
    GoalNotFoundError,
    InvalidRuleFormatError,
)
from LogiShell0.exceptions import FileNotFoundError as ESFileNotFoundError


KB_PATH = os.path.join(os.path.dirname(__file__), "", "animal_kb.json")

DIVIDER = "═" * 72


# ===========================================================================
# Helper
# ===========================================================================

def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


# ===========================================================================
# 1. Load and inspect the Knowledge Base
# ===========================================================================

def demo_kb_summary() -> None:
    section("1 — Knowledge Base Summary")
    kb = KnowledgeBase(KB_PATH)
    print(kb.summary())
    print(f"\n  Rule count   : {len(kb.rules)}")
    print(f"  Initial facts: {sorted(kb.initial_facts)}")


# ===========================================================================
# 2. Forward Chaining — full closure
# ===========================================================================

def demo_forward_chaining() -> None:
    section("2 — Forward Chaining (full closure)")

    # Seed WM with animal-specific attributes on top of the KB's initial facts
    extra = {
        "has_tawny_color",
        "has_dark_spots",
        "eats_meat",
    }

    session = Session(KB_PATH, extra_facts=extra)
    print(f"\n  Extra runtime facts: {sorted(extra)}")
    print(f"  KB initial facts   : {sorted(session.kb.initial_facts)}")

    result = session.run_forward()
    result.print_trace()

    print("  ── Summary ──")
    print(f"  Mode          : {result.mode.name}")
    print(f"  Success       : {result.success}")
    print(f"  Fired rules   : {result.fired_rules}")
    print(f"  New facts     : {sorted(result.new_facts)}")
    print(f"  Final WM      : {sorted(result.derived_facts)}")


# ===========================================================================
# 3. Backward Chaining — prove a specific goal
# ===========================================================================

def demo_backward_chaining_success() -> None:
    section("3 — Backward Chaining (goal = 'is_cheetah', expected: SUCCESS)")

    extra = {
        "has_tawny_color",
        "has_dark_spots",
        "eats_meat",
    }

    session = Session(KB_PATH, extra_facts=extra)
    result = session.run_backward(goal="is_cheetah")
    result.print_trace()

    print("  ── Summary ──")
    print(f"  Goal    : {result.goal}")
    print(f"  Proven  : {result.success}")
    print(f"  Fired   : {result.fired_rules}")


def demo_backward_chaining_failure() -> None:
    section("4 — Backward Chaining (goal = 'is_penguin', expected: FAILURE)")

    # No facts that would support is_penguin (cannot_fly + swims_well missing)
    session = Session(KB_PATH)
    result = session.run_backward(goal="is_penguin")
    result.print_trace()

    print("  ── Summary ──")
    print(f"  Goal    : {result.goal}")
    print(f"  Proven  : {result.success}")


def demo_backward_chaining_bird() -> None:
    section("5 — Backward Chaining (goal = 'is_bird', expected: SUCCESS via R4)")

    # has_feathers is already an initial fact in the KB → trivially proven
    session = Session(KB_PATH)
    result = session.run_backward(goal="is_bird")
    result.print_trace()


# ===========================================================================
# 4. Conflict resolution demo
# ===========================================================================

def demo_conflict_resolution() -> None:
    section("6 — Conflict Resolution (most specific rule wins)")

    print(
        "\n  Rules R1, R2, and R3 all conclude 'is_mammal', but:\n"
        "    R1 has 1 premise  (has_hair)\n"
        "    R2 has 1 premise  (gives_milk)\n"
        "    R3 has 2 premises (has_hair ∧ gives_milk)  ← most specific\n"
        "\n  When both has_hair AND gives_milk are in WM, R3 must be\n"
        "  selected over R1 and R2.\n"
    )

    # Both premises of R3 are already in the KB's initial facts
    session = Session(KB_PATH)
    result = session.run_forward()

    conflict_entries = [
        e for e in result.trace
        if "CONFLICT_RESOLVED" in e.event_type.value
    ]
    for entry in conflict_entries:
        print(f"  {entry}")


# ===========================================================================
# 5. Error handling demos
# ===========================================================================

def demo_error_handling() -> None:
    section("7 — Error Handling")

    # --- 7a. File not found ---
    print("\n  7a. FileNotFoundError:")
    try:
        KnowledgeBase("non_existent_file.json")
    except ESFileNotFoundError as exc:
        print(f"    ✓ Caught FileNotFoundError: {exc}")

    # --- 7b. Goal not in KB ---
    print("\n  7b. GoalNotFoundError:")
    try:
        session = Session(KB_PATH)
        session.run_backward("is_dragon")
    except GoalNotFoundError as exc:
        print(f"    ✓ Caught GoalNotFoundError: {exc}")

    # --- 7c. Invalid JSON KB ---
    import tempfile, json
    print("\n  7c. InvalidRuleFormatError (missing 'conclusion'):")
    bad_kb = {
        "facts": ["f1"],
        "rules": [
            {"id": "R1", "premises": ["f1"]}   # <-- missing 'conclusion'
        ]
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as tmp:
        json.dump(bad_kb, tmp)
        tmp_path = tmp.name

    try:
        KnowledgeBase(tmp_path)
    except InvalidRuleFormatError as exc:
        print(f"    ✓ Caught InvalidRuleFormatError: {exc}")
    finally:
        os.unlink(tmp_path)


# ===========================================================================
# 6. Session history
# ===========================================================================

def demo_session_history() -> None:
    section("8 — Session History (multiple runs on the same Session)")

    session = Session(
        KB_PATH,
        extra_facts={"has_tawny_color", "has_dark_spots", "eats_meat"},
    )
    session.run_forward()
    session.run_backward("is_cheetah")
    session.run_backward("is_ostrich")
    session.print_history_summary()


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    print(f"\n{'╔' + '═'*70 + '╗'}")
    print(f"{'║':1}{'Propositional Logic Expert System — Demo':^70}{'║':1}")
    print(f"{'╚' + '═'*70 + '╝'}")

    demo_kb_summary()
    demo_forward_chaining()
    demo_backward_chaining_success()
    demo_backward_chaining_failure()
    demo_backward_chaining_bird()
    demo_conflict_resolution()
    demo_error_handling()
    demo_session_history()

    print(f"\n{'═'*72}")
    print("  Demo complete.")
    print(f"{'═'*72}\n")
