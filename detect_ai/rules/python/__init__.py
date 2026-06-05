"""Python-specific detection rules."""

from .comments import CommentsRule
from .complexity import ComplexityRule
from .docstrings import DocstringsRule
from .error_handling import ErrorHandlingRule
from .formatting import FormattingRule
from .naming import NamingRule
from .redundant_patterns import RedundantPatternsRule
from .structural_patterns import StructuralPatternsRule
from .syntax_preferences import SyntaxPreferenceRule
from .type_hints import TypeHintsRule

__all__ = [
    "NamingRule",
    "DocstringsRule",
    "TypeHintsRule",
    "SyntaxPreferenceRule",
    "CommentsRule",
    "FormattingRule",
    "ComplexityRule",
    "ErrorHandlingRule",
    "RedundantPatternsRule",
    "StructuralPatternsRule",
]
