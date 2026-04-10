"""
expert_system
=============
A professional Propositional Logic (Order-0) Expert System Shell.

Public API
----------
.. code-block:: python

    from expert_system import Session, KnowledgeBase, InferenceEngine
    from expert_system import Rule, InferenceResult, ChainingMode
    from expert_system.exceptions import (
        ExpertSystemError,
        KnowledgeBaseError,
        InvalidRuleFormatError,
        GoalNotFoundError,
    )

Quick start
-----------
.. code-block:: python

    session = Session("my_kb.json")
    session.run_forward().print_trace()
    session.run_backward("some_goal").print_trace()
"""

from .exceptions import (
    ExpertSystemError,
    GoalNotFoundError,
    InferenceError,
    InvalidRuleFormatError,
    KnowledgeBaseError,
)
from .inference_engine import InferenceEngine
from .knowledge_base import KnowledgeBase
from .models import ChainingMode, InferenceResult, Rule, TraceEntry, TraceEventType
from .session import Session

__all__ = [
    # Main entry point
    "Session",
    # Core components
    "KnowledgeBase",
    "InferenceEngine",
    # Data models
    "Rule",
    "InferenceResult",
    "TraceEntry",
    "TraceEventType",
    "ChainingMode",
    # Exceptions
    "ExpertSystemError",
    "KnowledgeBaseError",
    "InvalidRuleFormatError",
    "InferenceError",
    "GoalNotFoundError",
]

__version__ = "1.0.0"
__author__ = "Senior AI & Python Engineer"
