"""Tests for detection rules."""

from detect_ai.analyzer import Analyzer
from detect_ai.rules.python.naming import NamingRule
from detect_ai.rules.python.syntax_preferences import SyntaxPreferenceRule

AI_CODE = '''
def process_user_data(user_list: list[dict], output_directory: str, verbose: bool = True) -> str | None:
    """
    Process a list of user dictionaries and write the result to a JSON file.

    Args:
        user_list: List of user dictionaries.
        output_directory: Directory to write output.
        verbose: Whether to print progress.

    Returns:
        Output path or None if input is empty.
    """
    if user_list is None:
        return None

    processed_results = []
    for user in user_list:
        if not user.get("is_active"):
            continue
        user_id = user["id"]
        user_name = user["name"]
        user_email = user["email"]
        processed_item = {"id": user_id, "name": user_name, "email": user_email, "status": "active"}
        processed_results.append(processed_item)

    if verbose:
        print(f"Processed {len(processed_results)} users")

    return output_directory
'''

HUMAN_CODE = """
def _process_user_data(arr, result, entity=True):
    # this is ugly, fix later
    if arr == None:
        return None
    val = []
    for row in arr:
        if not row.get("is_active"):
            continue
        tmp50 = row["id"]
        row1 = tmp50
        word = row['name']
        thing = row["email"]
        o =  {"id": row1, "name": word, "email": thing, 'status': 'active'}
        val.append(o)
    return result
"""

# Truly organic human code — mixed naming, inconsistent style, abbreviations
ORGANIC_HUMAN_CODE = """
def calc_stuff(foo, flag):
    # FIXME: this is broken on weekends
    if foo == None:
        return
    out = []
    for bar in foo:
        if not bar["ok"]:
            continue
        baz = bar["name"]
        qux = bar["email"]
        item = {"name": baz, "email": qux}
        out.append(item)
    print("done")
    return out
"""


def test_ai_code_scores_high():
    analyzer = Analyzer()
    report = analyzer.analyze_source(AI_CODE, "ai_sample.py")
    assert (
        report.overall_score > 50
    ), f"Expected AI code to score >50, got {report.overall_score}"


def test_human_code_scores_low():
    analyzer = Analyzer()
    report = analyzer.analyze_source(HUMAN_CODE, "human_sample.py")
    assert (
        report.overall_score < 50
    ), f"Expected human code to score <50, got {report.overall_score}"


def test_naming_rule_detects_ai():
    rule = NamingRule()
    import ast

    tree = ast.parse(AI_CODE)
    result = rule.analyze(AI_CODE, tree)
    assert result.score > 50, f"Naming should flag AI code, got {result.score}"


def test_naming_rule_detects_human():
    rule = NamingRule()
    import ast

    tree = ast.parse(ORGANIC_HUMAN_CODE)
    result = rule.analyze(ORGANIC_HUMAN_CODE, tree)
    assert result.score < 50, f"Naming should flag human code, got {result.score}"


def test_syntax_rule_detects_is_none():
    rule = SyntaxPreferenceRule()
    import ast

    tree = ast.parse(AI_CODE)
    result = rule.analyze(AI_CODE, tree)
    assert result.score > 50, f"Syntax should flag is None usage, got {result.score}"
