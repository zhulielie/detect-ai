<div align="center">

# 🔍 detect-ai

**[deai](https://github.com/zhulielie/deai/blob/main/README.zh-CN.md) 的宿敌。**

*通过多层 AST 指纹、统计分析和对抗硬化，检测 AI 生成的源代码。*

[🇺🇸 English](README.md)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](https://github.com/zhulielie/detect-ai/actions)
[![VS Code](https://img.shields.io/badge/VS%20Code-Extension-blueviolet.svg)](./vscode)
[![Web UI](https://img.shields.io/badge/Web-UI-orange.svg)](./web)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](./Dockerfile)
[![在线体验](https://img.shields.io/badge/在线体验-00C7B7.svg)](https://detect-ai-neur.onrender.com/)
[![Gitee Stars](https://gitee.com/zhulielie/detect-ai/badge/star.svg?theme=dark)](https://gitee.com/zhulielie/detect-ai/stargazers)
[![Gitee Forks](https://gitee.com/zhulielie/detect-ai/badge/fork.svg?theme=dark)](https://gitee.com/zhulielie/detect-ai/members)

</div>

---

## 🎯 它能做什么

现代 AI 编程助手（ChatGPT、Claude、Copilot、Cursor）生成的代码带有**可识别的指纹**：

| AI 指纹 | 人类代码 |
|---------|---------|
| 每个函数都有完美的 docstring | 缺失或只有一行注释 |
| 到处用 `is None` | 混用 `== None` |
| 100% f-string | 还有 `.format()` 和 `%` |
| 列表推导式 | 显式 `for` + `append` 循环 |
| 间距完美一致 | 运算符空格随机松紧 |
| 描述性命名（`processed_user_data_list`） | `tmp`、`buf`、`i` |
| 零 TODO/FIXME/HACK | 沮丧吐槽注释 |
| 完美的错误处理 | 裸 `except:` 或干脆没有 |

**detect-ai** 通过 **10 条 AST 规则 + 统计分析** 提取这些指纹，给出 0-100 的 AI 指数评分。

---

## ⚔️ 与 deai 的对抗

我们构建 **detect-ai** 就是为了对抗 **[deai](https://github.com/zhulielie/deai/blob/main/README.zh-CN.md)** —— 一个把 AI 代码伪装成人类代码的"去 AI 化"工具。

### 第一轮 — deai 伪装前后对比

| detect-ai 规则 | 原始 AI 代码 | deai 伪装后 | 残留检测 |
|----------------|-------------|-------------|---------|
| naming | 90.0 | **55.0** | 🔴 检测到 deai 命名池碰撞 |
| docstrings | 100.0 | **30.0** | — |
| type_hints | 95.0 | **35.0** | — |
| **syntax_preferences** | **85.0** | **85.0** | ✅ **纹丝不动 — 深层 AST 信号** |
| comments | 40.0 | **30.0** | — |
| formatting | 80.0 | **60.0** | — |
| complexity | 35.0 | **35.0** | — |
| error_handling | 50.0 | **50.0** | — |
| **redundant_patterns** | **40.0** | **67.0** | ✅ **反向检测 — 抓到 deai 注入痕迹** |
| structural_patterns | 40.0 | **50.0** | ✅ **函数长度均匀性暴露** |
| **总分** | **65.69** | **50.79** | ✅ **仍处于不确定/AI 区间** |

> **核心发现**：deai 能伪装表面特征（命名、文档、类型），但**深层语法偏好（`is None`、f-string）**和**统计均匀性**会在 AST 变换中幸存下来。detect-ai 抓住了 deai 藏不住的东西。

---

## 🏆 真实项目扫描结果

我们在自己的项目上跑了一遍 detect-ai：

| 项目 | 语言 | 文件数 | 平均分 | 判定 |
|------|------|--------|--------|------|
| **douyinchajian** | JS/Python | 8 | **65.3** | likely_ai 🔴 |
| **bytebot** | TS | 146 | **56.7** | uncertain 🟡 |
| **chromemcp** | JS | 16 | **61.4** | likely_ai 🔴 |
| **ai-analysis-code-reference** | Python | ? | **68.6** | likely_ai 🔴 |
| **aimodule** | Python | 3241 | **53.8** | uncertain 🟡 |
| **comfyui-mcp-server** | Python | 15 | **57.3** | uncertain 🟡 |

**最高风险文件：**
- `bytebot/useWebSocket.ts` — **78.6** 🤖
- `bytebot/agent.processor.ts` — **74.1** 🤖
- `chromemcp/click-helper.js` — **72.1** 🤖
- `douyinchajian/popup.js` — **72.1** 🤖

---

## 🚀 快速开始

### CLI

```bash
pip install detect-ai

# 扫描单个文件
python -m detect_ai scan app.py -v

# 扫描整个目录（支持 Python + JS/TS）
python -m detect_ai scan ./src --recursive

# Markdown 报告
python -m detect_ai scan src/ --format markdown --output AI_REPORT.md

# Shield Badge
python -m detect_ai scan src/ --format badge --output badge.svg

# JSON（CI 集成）
python -m detect_ai scan src/ --format json --output report.json

# CI 阈值 — 超过则 exit 1
python -m detect_ai scan src/ --threshold 75
```

### Web UI

**在线体验**: https://detect-ai-neur.onrender.com/

```bash
pip install ".[web]"
python web/app.py
# → http://localhost:5001
```

- 粘贴代码 → **分析**
- 上传 ZIP / 扫描本地路径
- **🛡️ 对抗模式** — 一键"用 deai 伪装后再检测"

### Docker

```bash
docker-compose up
# → http://localhost:5001
```

### VS Code 扩展

```bash
cd vscode
npm install
npm run compile
```

支持命令：
- `detect-ai: 扫描当前文件`
- `detect-ai: 扫描选中代码`
- `detect-ai: 扫描工作区`
- 状态栏实时显示 AI 分数

---

## 🔬 检测规则（10 条）

### Python（10 条）

| 规则 | 权重 | AI 指纹 | 抗 deai |
|------|------|--------|---------|
| **naming** | 1.2 | 长描述性名称、类型嵌入（`name_str`） | 检测 deai 命名池碰撞 |
| **docstrings** | 1.0 | 100% 覆盖率、Google/NumPy 结构化风格 | — |
| **type_hints** | 1.0 | 全参数+返回值注解 | — |
| **syntax_preferences** | 1.1 | `is None`、f-string、列表推导式 | **deai 无法伪造的深层信号** |
| **comments** | 0.9 | 零 TODO/FIXME、拼写完美 | — |
| **formatting** | 0.8 | 引号统一、空格完美、无 trailing ws | — |
| **complexity** | 0.9 | 嵌套深度均匀、try/except 一致 | — |
| **error_handling** | 1.0 | 具体异常类型、`raise from`、finally | 检测被剥离的错误处理 |
| **redundant_patterns** | 1.3 | 干净代码 | **检测 deai 注入的冗余模式** |
| **structural_patterns** | 1.0 | 函数长度 CV<0.35 | **全局统计指纹** |

### JavaScript / TypeScript（3 条）

| 规则 | AI 指纹 |
|------|--------|
| **js_naming** | 严格 camelCase、冗长命名 |
| **js_syntax_preferences** | 只用 const/let、箭头函数、模板字符串、可选链 |
| **js_formatting** | 严格 `===`、分号/引号风格一致 |

### Git 历史（1 个模块）

| 信号 | 伪造检测 |
|------|---------|
| **GitDetector** | 提交间隔均匀、消息熵低、周末回避、单作者完美历史 |

---

## 🧠 架构

```
输入（源代码）
    ↓
语言检测器 ──→ Python / JavaScript / TypeScript
    ↓
AST 解析 ─────────────────────────────────────┐
    ↓                                           │
规则引擎（并行）                                 │
├── naming.py           （标识符熵）            │
├── docstrings.py       （覆盖率+结构）          │
├── type_hints.py       （注解密度）             │
├── syntax_preferences  （is None、f-string、   │
│                        listcomp、walrus）      │
├── comments.py         （TODO/FIXME/拼写）      │
├── formatting.py       （引号、空格、          │
│                        trailing ws）           │
├── complexity.py       （嵌套方差）             │
├── error_handling.py   （裸 except、空         │
│                        处理块）                │
├── redundant_patterns  （== True、临时变量链、  │
│                        list(genexpr)）         │
└── structural_patterns （函数长度 CV、        │
                         参数 CV、import 块）   │
    ↓                                           │
评分引擎 ──→ 加权平均 ──→ 0-100               │
    ↓                                           │
判定 ──→ human / likely_human / uncertain /     │
        likely_ai / ai                          │
    ↓                                           │
报告器 ──→ text / json / markdown / badge.svg   │
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

超过阈值会自动在 PR 下评论报警。

---

## 📊 评分体系

| 分数 | 级别 | Emoji | 含义 |
|------|------|-------|------|
| 0-20 | human | 🧑‍💻 | 强烈人类 |
| 21-40 | likely_human | 👤 | 可能人类 |
| 41-60 | uncertain | ❓ | 混合/难以判断 |
| 61-80 | likely_ai | 🤖 | 明显 AI 特征 |
| 81-100 | ai | 🤖🤖 | 强烈 AI 生成 |

---

## 🤝 贡献

核心文件：

| 文件 | 作用 |
|------|------|
| `detect_ai/rules/python/*.py` | AST 检测规则 |
| `detect_ai/rules/javascript/*.py` | JS/TS 规则（基于正则） |
| `detect_ai/git_detector.py` | Git 历史伪造检测 |
| `detect_ai/scoring.py` | 加权评分引擎 |
| `detect_ai/reporters/` | 输出格式化 |
| `detect_ai/cli.py` | CLI 入口 |
| `web/app.py` | Flask Web UI |
| `vscode/` | VS Code 扩展 |

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

> *此工具是 deai 的阴阳之阳。请负责任地使用。*

如果觉得项目有用，请在 [GitHub](https://github.com/zhulielie/detect-ai) 或 [Gitee](https://gitee.com/zhulielie/detect-ai) 上点一颗 ⭐！

[![Star History Chart](https://api.star-history.com/svg?repos=zhulielie/detect-ai&type=Date)](https://star-history.com/#zhulielie/detect-ai&Date)

</div>
