<div align="center">

# 🔍 detect-ai

**The antagonist of [deai](https://github.com/zhuli/deai).**

*Detect AI-generated source code through multi-layer AST fingerprinting, statistical analysis, and adversarial hardening.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/zhuli/detect-ai/actions)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blueviolet.svg)](./vscode)
[![Web UI](https://img.shields.io/badge/Web-UI-orange.svg)](./web)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](./Dockerfile)
[![Live Demo](https://img.shields.io/badge/Live-Demo-00C7B7.svg)](https://detect-ai-neur.onrender.com/)

</div>

---

## 🎯 What It Does

Modern AI coding assistants (ChatGPT, Claude, Copilot, Cursor) generate code with **detectable fingerprints**:

| AI Fingerprint | Human Counterpart |
|----------------|-------------------|
| Perfect docstrings on every function | Missing or one-liner docs |
| `is None` everywhere | `== None` mixed in |
| 100% f-strings | `.format()` and `%` still around |
| List comprehensions | Explicit `for` + `append` loops |
| Consistent spacing | Random tight/loose operators |
| Descriptive names (`processed_user_data_list`) | `tmp`, `buf`, `i` |
| Zero TODO/FIXME/HACK | Frustrated comments |
| Perfect error handling | Bare `except:` or nothing |

**detect-ai** extracts these fingerprints through **10 AST rules + statistical analysis** and gives a 0-100 AI score.

---

## ⚔️ Adversarial: detect-ai vs deai

We built **detect-ai** specifically to fight **[deai](https://github.com/zhuli/deai)** — an AI code humanizer that strips fingerprints.

### Round 1 — Before vs After deai Humanization

| detect-ai Rule | AI Code | After deai | Residual Detection |
|----------------|---------|------------|-------------------|
| naming | 90.0 | **55.0** | 🔴 deai pools detected |
| docstrings | 100.0 | **30.0** | — |
| type_hints | 95.0 | **35.0** | — |
| **syntax_preferences** | **85.0** | **85.0** | ✅ **Unchanged — deep AST signal** |
| comments | 40.0 | **30.0** | — |
| formatting | 80.0 | **60.0** | — |
| complexity | 35.0 | **35.0** | — |
| error_handling | 50.0 | **50.0** | — |
| **redundant_patterns** | **40.0** | **67.0** | ✅ **Inverse detection — deai artifacts caught** |
| structural_patterns | 40.0 | **50.0** | ✅ **Function-length uniformity caught** |
| **OVERALL** | **65.69** | **50.79** | ✅ **Still in uncertain/AI territory** |

> **Key insight**: deai can fake surface features (names, docs, types), but **deep syntax preferences (`is None`, f-strings)** and **statistical uniformity** survive AST transforms. detect-ai catches what deai cannot hide.

---

## 🏆 Real-World Scan Results

We ran detect-ai across our own projects. Here's what we found:

| Project | Lang | Files | Avg Score | Verdict |
|---------|------|-------|-----------|---------|
| **douyinchajian** | JS/Python | 8 | **65.3** | likely_ai 🔴 |
| **bytebot** | TS | 146 | **56.7** | uncertain 🟡 |
| **chromemcp** | JS | 16 | **61.4** | likely_ai 🔴 |
| **ai-analysis-code-reference** | Python | ? | **68.6** | likely_ai 🔴 |
| **aimodule** | Python | 3241 | **53.8** | uncertain 🟡 |
| **comfyui-mcp-server** | Python | 15 | **57.3** | uncertain 🟡 |

**Highest risk files detected:**
- `bytebot/useWebSocket.ts` — **78.6** 🤖
- `bytebot/agent.processor.ts` — **74.1** 🤖
- `chromemcp/click-helper.js` — **72.1** 🤖
- `douyinchajian/popup.js` — **72.1** 🤖

---

## 🚀 Quick Start

### CLI

```bash
pip install detect-ai

# Single file
python -m detect_ai scan app.py -v

# Entire directory (Python + JS/TS)
python -m detect_ai scan ./src --recursive

# Markdown report
python -m detect_ai scan src/ --format markdown --output AI_REPORT.md

# Shield badge for README
python -m detect_ai scan src/ --format badge --output badge.svg

# CI threshold — exit 1 if any file > 75
python -m detect_ai scan src/ --threshold 75
```

### Web UI

**在线体验**: https://detect-ai-neur.onrender.com/

```bash
pip install ".[web]"
python web/app.py
# → http://localhost:5001
```

- Paste code → **Analyze**
- Upload ZIP / scan local path
- **🛡️ Adversarial Mode** — one-click "humanize with deai then re-detect"

### Docker

```bash
docker-compose up
# → http://localhost:5001
```

### VS Code Extension

```bash
cd vscode
npm install
npm run compile
```

Commands:
- `detect-ai: Scan Current File`
- `detect-ai: Scan Selection`
- `detect-ai: Scan Workspace`
- Status bar shows real-time AI score

---

## 🔬 Detection Rules (10 Rules)

### Python (10 rules)

| Rule | Weight | AI Fingerprint | Anti-deai |
|------|--------|---------------|-----------|
| **naming** | 1.2 | Long names, type-embedded (`name_str`) | Detects deai name-pool clustering |
| **docstrings** | 1.0 | 100% coverage, Google/NumPy style | — |
| **type_hints** | 1.0 | All params + returns annotated | — |
| **syntax_preferences** | 1.1 | `is None`, f-strings, listcomps | **Deep signal — deai can't fake** |
| **comments** | 0.9 | Zero TODO/FIXME, perfect spelling | — |
| **formatting** | 0.8 | Consistent quotes, perfect spacing | — |
| **complexity** | 0.9 | Uniform nesting depth | — |
| **error_handling** | 1.0 | Specific exceptions, `raise from` | Detects stripped error handling |
| **redundant_patterns** | 1.3 | Clean code | **Detects deai injection artifacts** |
| **structural_patterns** | 1.0 | Uniform function lengths (CV<0.35) | **Global statistical fingerprint** |

### JavaScript / TypeScript (3 rules)

| Rule | AI Fingerprint |
|------|---------------|
| **js_naming** | Strict camelCase, verbose names |
| **js_syntax_preferences** | const/let only, arrow functions, template literals, optional chaining |
| **js_formatting** | Strict `===`, consistent semicolons/quote style |

### Git History (1 module)

| Signal | Forgery Detection |
|--------|-------------------|
| **GitDetector** | Uniform commit spacing, low message entropy, weekend avoidance, single-author perfection |

---

## 🧠 Architecture

```
Input (Source Code)
    ↓
Language Detector ──→ Python / JavaScript / TypeScript
    ↓
AST Parse ─────────────────────────────────────┐
    ↓                                           │
Rule Engine (parallel)                         │
├── naming.py           (identifier entropy)   │
├── docstrings.py       (coverage + structure) │
├── type_hints.py       (annotation density)   │
├── syntax_preferences  (is None, f-string,    │
│                        listcomp, walrus)     │
├── comments.py         (TODO/FIXME/typos)     │
├── formatting.py       (quotes, spacing,      │
│                        trailing ws)           │
├── complexity.py       (nesting variance)     │
├── error_handling.py   (bare except, empty    │
│                        handlers)              │
├── redundant_patterns  (== True, temp chains, │
│                        list(genexpr))         │
└── structural_patterns (function-length CV,   │
                         param CV, import       │
                         block analysis)        │
    ↓                                           │
Scoring Engine ──→ weighted average ──→ 0-100  │
    ↓                                           │
Verdict ──→ human / likely_human / uncertain /  │
            likely_ai / ai                      │
    ↓                                           │
Reporter ──→ text / json / markdown / badge.svg │
```

---

## 🛡️ GitHub Action

```yaml
name: Detect AI Code

on: [push, pull_request]

jobs:
  detect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: zhuli/detect-ai@main
        with:
          path: .
          threshold: 75
          format: markdown
          verbose: true
          git-check: true
```

Auto-posts PR comment if AI score exceeds threshold.

---

## 📊 Scoring System

| Score | Level | Emoji | Meaning |
|-------|-------|-------|---------|
| 0-20 | human | 🧑‍💻 | Strongly human |
| 21-40 | likely_human | 👤 | Probably human |
| 41-60 | uncertain | ❓ | Mixed / ambiguous |
| 61-80 | likely_ai | 🤖 | AI fingerprints detected |
| 81-100 | ai | 🤖🤖 | Strong AI signature |

---

## 🗺️ Roadmap

- [x] Python AST rule engine (10 rules)
- [x] JavaScript / TypeScript support
- [x] Adversarial hardened rules (anti-deai)
- [x] CLI with JSON / Markdown / Badge output
- [x] Flask Web UI (single file + ZIP + local path)
- [x] 🛡️ Adversarial mode (deai integration)
- [x] Git history forgery detector
- [x] VS Code extension
- [x] Docker + docker-compose
- [x] GitHub Action
- [ ] Pre-commit hook
- [ ] ML classifier (scikit-learn ensemble)
- [ ] Cross-file consistency analysis
- [ ] Java / Go / Rust support

---

## 🤝 Contributing

Core files:

| File | Purpose |
|------|---------|
| `detect_ai/rules/python/*.py` | AST detection rules |
| `detect_ai/rules/javascript/*.py` | JS/TS rules (regex-based) |
| `detect_ai/git_detector.py` | Git history forgery detection |
| `detect_ai/scoring.py` | Weighted scoring engine |
| `detect_ai/reporters/` | Output formatters |
| `detect_ai/cli.py` | CLI entrypoint |
| `web/app.py` | Flask web UI |
| `vscode/` | VS Code extension |

```bash
pip install -e ".[dev,web]"
pytest -v
black detect_ai/ tests/ web/
mypy detect_ai/
ruff check detect_ai/ tests/ web/
```

---

## 📄 License

MIT

---

<div align="center">

> *This tool is the yang to deai's yin. Use responsibly.*

If you find this project useful, give it a ⭐ on GitHub!

</div>
