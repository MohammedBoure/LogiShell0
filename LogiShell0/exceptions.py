"""
exceptions.py
-------------
Custom exception hierarchy for the Expert System library.

All library-specific errors inherit from ``ExpertSystemError`` so that
callers can catch the entire family with a single except clause.
"""


class ExpertSystemError(Exception):
    """Base class for all Expert System exceptions."""


class KnowledgeBaseError(ExpertSystemError):
    """Raised when the Knowledge Base cannot be loaded or validated."""


class FileNotFoundError(KnowledgeBaseError):  # noqa: A001  (shadows built-in intentionally)
    """Raised when the specified JSON knowledge-base file does not exist."""


class InvalidRuleFormatError(KnowledgeBaseError):
    """
    Raised when a rule entry in the JSON file is structurally invalid.

    Examples of invalid rules
    -------------------------
    - Missing required keys ('id', 'premises', 'conclusion').
    - 'premises' is not a list.
    - 'conclusion' is not a non-empty string.
    - Duplicate rule IDs.
    """


class InferenceError(ExpertSystemError):
    """Raised when the inference engine encounters an unrecoverable error."""


class GoalNotFoundError(InferenceError):
    """
    Raised when backward chaining is invoked with a goal that does not
    appear in any rule conclusion AND is not an initial fact.
    """
