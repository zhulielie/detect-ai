"""JavaScript/TypeScript detection rules."""

from .naming import JSNamingRule
from .syntax_preferences import JSSyntaxPreferenceRule
from .formatting import JSFormattingRule

__all__ = [
    "JSNamingRule",
    "JSSyntaxPreferenceRule",
    "JSFormattingRule",
]
