# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Install in editable mode with all extras:
```bash
pip install -e ".[dev,web]"
```

Run the CLI:
```bash
python -m detect_ai scan <path> [-r] [-v] [--format text|json|markdown|badge]
```

Run the Web UI:
```bash
python web/app.py
# → http://localhost:5001
```

Lint, type-check, and test:
```bash
black detect_ai/ tests/ web/
mypy detect_ai/
ruff check detect_ai/ tests/ web/
pytest -v
```

## Architecture Overview

**detect-ai** is a Python CLI + Web tool that detects AI-generated source code through static AST analysis and heuristic fingerprinting. It is the antagonist of [deai](https://github.com/zhulielie/deai).

### Detection Pipeline

1. **Language dispatch** — `Analyzer` selects rules based on file extension (`.py` → Python, `.js/.ts` → JavaScript).
2. **AST parse** — Python code is parsed with `ast.parse`; JS/TS uses regex-based analysis (no AST parser dependency).
3. **Rule evaluation** — Each rule scores 0-100 (higher = more AI-like) with a confidence value.
4. **Scoring** — `ScoreReport.from_results()` computes a weighted average and assigns a verdict:
   - 0-20: human
   - 21-40: likely_human
   - 41-60: uncertain
   - 61-80: likely_ai
   - 81-100: ai

### Python Rules (`detect_ai/rules/python/`)

| Rule | Weight | What it detects |
|------|--------|----------------|
| naming | 1.2 | Long descriptive names, type-embedded names, deai name-pool clustering |
| docstrings | 1.0 | Perfect coverage, Google/NumPy structured style |
| type_hints | 1.0 | All params + returns annotated |
| syntax_preferences | 1.1 | `is None`, f-strings, listcomps, walrus operator |
| comments | 0.9 | Zero TODO/FIXME, perfect spelling, no emotional markers |
| formatting | 0.8 | Consistent quotes, perfect spacing, no trailing whitespace |
| complexity | 0.9 | Uniform nesting depth, consistent try/except usage |
| error_handling | 1.0 | Specific exceptions, `raise from`, finally blocks |
| redundant_patterns | 1.3 | `== True`, temp variable chains, `list(genexpr)` — deai artifacts |
| structural_patterns | 1.0 | Uniform function-length CV, param CV, import block analysis |

### JavaScript/TypeScript Rules (`detect_ai/rules/javascript/`)

Regex-based analysis (no AST parser dependency):
- **js_naming** — camelCase consistency, verbose names
- **js_syntax_preferences** — const/let vs var, arrow functions, template literals, optional chaining
- **js_formatting** — `===` vs `==`, semicolon consistency, quote style

### Git History Detector (`detect_ai/git_detector.py`)

Analyzes `.git` metadata for forged commit histories:
- Message pattern matching against known forge pools
- Time distribution uniformity
- Weekend avoidance
- Commit spacing CV
- Author consistency
- Message entropy

### Extension Points

- **New Python rule** — subclass `BaseRule` in `detect_ai/rules/base.py`, implement `analyze(source, tree, path)`, register in `detect_ai/analyzer.py`.
- **New JS rule** — same pattern, but use regex on `source` string instead of AST.
- **New language** — add rules under `detect_ai/rules/<lang>/`, register in `Analyzer.DEFAULT_RULES`.
- **New reporter** — implement in `detect_ai/reporters/`, add format to CLI choices.

## Project Layout

- `detect_ai/cli.py` — argparse entry point
- `detect_ai/analyzer.py` — rule dispatcher
- `detect_ai/scoring.py` — weighted scoring + verdict engine
- `detect_ai/rules/python/*.py` — Python AST detection rules
- `detect_ai/rules/javascript/*.py` — JS/TS regex-based rules
- `detect_ai/git_detector.py` — Git history forgery detection
- `detect_ai/reporters/` — output formatters (text, json, markdown, badge)
- `web/app.py` — Flask Web UI with adversarial mode
- `web/templates/index.html` — i18n single-page app (zh/en)
- `vscode/` — VS Code extension
- `pyproject.toml` — setuptools build config
