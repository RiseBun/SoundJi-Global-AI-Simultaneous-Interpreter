# SoundJi - Global AI Simultaneous Interpreter

## 项目简介

SoundJi 是一个面向技术分享、网课和跨语言会议场景的 AI 同声传译助手。Day 1 版本先交付 P0 mock proof chain，用于证明“术语可控、状态可追踪、证据可复盘”的最小工程闭环。

当前版本不是生产级同传应用，不接真实 ASR、真实 LLM/翻译模型或真实会议平台。它先用可复现的 mock 数据、校验脚本、runner 和 transcript 证明核心链路。

当前 P0 闭环：

```text
SampleStream
-> ASREvent partial/final
-> TermEntry / TermHit
-> TimelineItem
-> Markdown / JSON ExportArtifact
```

## 议题方向

- AI 同声传译助手
- 语音交互与实时字幕状态
- 术语表/热词约束
- AI-native 工程证据链
- XEngineer / ZGC Vibe Coding 项目实践

## Day 1 分工记录

当前仓库由队友 `RiseBun` 创建并维护，我以仓库合作者身份在功能分支 `feature/day1-evidence-package` 合入 Day 1 工程证据包。

| 成员 | Day 1 分工 | 当前证据 |
|---|---|---|
| RiseBun / 仓库创建者 | 创建 GitHub 仓库、提供协作入口、后续负责合并 PR 和主分支维护 | GitHub 仓库 `RiseBun/SoundJi-Global-AI-Simultaneous-Interpreter` |
| 我 / 仓库合作者 | 梳理赛题与 XEngineer/ZGC 方法论，生成技术文档分类、P0 mock 数据、校验脚本、mock runner、transcript 输出和 PR/commit 证据文档 | `README.md`、`docs/ai_interpreter/*.md`、`mock_data/ai_interpreter/*.json`、`scripts/*.py`、`outputs/ai_interpreter/*` |
| 后续共同任务 | 在 PR 中审查 Day 1 证据包，确认主分支合并后仍可运行，再拆 P1 adapter 和 demo polish | `docs/ai_interpreter/05_day1_pr_commit_evidence.md` |

## 核心功能

- 使用固定英文技术分享 mock stream 模拟同传输入。
- 使用 partial/final ASR 事件区分不稳定字幕和稳定字幕。
- 使用术语表约束关键技术词，如 RAG、API、vector database、embedding、latency。
- 生成双语时间轴，记录英文原文、中文译文、时间范围和术语命中。
- 导出 Markdown transcript 和 JSON transcript。
- 覆盖 ASR、translation、export、glossary 四类 fallback。

## 技术文档分类

本仓库的技术文档放在 `docs/ai_interpreter/` 下，按“技术提案、架构设计、实现设计、MVP 分析、交接和 PR 证据”分类。

| 文档 | 类型 | 作用 |
|---|---|---|
| `00_project_handoff.md` | 项目交接说明 | 说明队友接手顺序、当前交付范围、P0/P1/P2 边界和风险 |
| `01_technical_proposal.md` | 技术提案 | 回答为什么做、为谁做、痛点证据、竞品/来源分级和 MVP 价值 |
| `02_architecture_design.md` | 架构设计 | 回答系统如何分层，定义 entry、task_object、agent_execution、tool_capability、governance、delivery 六层边界 |
| `03_implementation_design.md` | 实现设计 | 回答对象、事件、状态、fallback、验收样例和实现前置契约 |
| `04_mvp_analysis.md` | MVP 分析 | 回答 72 小时内做什么、P0/P1/P2 如何取舍、demo 和验收 checklist |
| `05_day1_pr_commit_evidence.md` | PR/commit 证据记录 | 记录 Day 1 PR 描述模板、commit 规划、无效红线自检、来源分级和后续 PR 拆分 |

三类设计文档边界：

```text
技术提案：回答 Why / For Whom / What Value
架构设计：回答 System How / Boundary / Module
实现设计：回答 Object / Event / State / Validation
```

## 技术栈和第三方依赖

当前 P0 版本只使用：

- Python 标准库
- Markdown 文档
- JSON mock 数据

当前未使用：

- React
- FastAPI
- OpenAI SDK
- LangChain
- Tailwind
- Whisper / FunASR / Vosk
- 数据库
- 真实会议平台 SDK

如后续接入任何第三方库、框架、模型 SDK 或历史代码片段，必须在 README 和对应 PR 描述中补充依赖来源、用途和原创功能边界。

## 原创功能说明

本项目当前原创部分是 P0 工程证据链设计和 mock demo 闭环，而不是某个真实 ASR 或翻译模型能力。

原创设计重点：

- 将“AI 同传”收敛为术语约束、字幕状态、时间轴和导出四个可验证能力。
- 用 `partial -> final` 事件表达实时字幕不稳定性，避免把临时识别结果直接写入最终复盘。
- 用术语命中记录证明不是简单的 ASR + 翻译 API 壳。
- 用 fallback 明确 ASR、翻译、导出、术语导入失败时的降级边界。
- 用 Markdown/JSON transcript 形成可交接、可复盘 artifact。

## 本地运行方式

从仓库根目录运行：

```powershell
python ".\scripts\validate_ai_interpreter_mock_data.py"
python ".\scripts\run_ai_interpreter_mock_demo.py"
```

macOS/Linux 可使用：

```bash
python scripts/validate_ai_interpreter_mock_data.py
python scripts/run_ai_interpreter_mock_demo.py
```

预期输出：

```text
AI interpreter mock data validation passed.
Summary: partials=10, finals=10, terms=10, timeline_items=10, fallbacks=asr/translation/export/glossary

AI interpreter mock demo transcript generated.
Summary: finals=10, glossary_entries=10, term_hits=13, ... optional_revision_demo_exists=true
```

## 测试方式

1. 运行 mock 数据校验脚本：

```powershell
python ".\scripts\validate_ai_interpreter_mock_data.py"
```

验收点：

- 四个 JSON 文件存在且可解析。
- partial 和 final 事件数量一致。
- 时间轴条数与 final 事件一致。
- 必需术语存在。
- fallback 覆盖 ASR、translation、export、glossary。

2. 运行 mock demo runner：

```powershell
python ".\scripts\run_ai_interpreter_mock_demo.py"
```

验收点：

- 生成 `outputs/ai_interpreter/transcript.md`。
- 生成 `outputs/ai_interpreter/transcript.json`。
- summary 显示 `finals=10`、`glossary_entries=10`、`term_hits=13`。
- P2 revision demo 只在 summary 标注，不进入主 timeline。

## 项目结构

```text
.
├── README.md
├── docs/
│   └── ai_interpreter/
│       ├── 00_project_handoff.md
│       ├── 01_technical_proposal.md
│       ├── 02_architecture_design.md
│       ├── 03_implementation_design.md
│       ├── 04_mvp_analysis.md
│       └── 05_day1_pr_commit_evidence.md
├── mock_data/
│   └── ai_interpreter/
│       ├── sample_stream.json
│       ├── term_glossary.json
│       ├── expected_timeline.json
│       └── fallback_examples.json
├── scripts/
│   ├── validate_ai_interpreter_mock_data.py
│   └── run_ai_interpreter_mock_demo.py
├── outputs/
│   └── ai_interpreter/
│       ├── transcript.md
│       └── transcript.json
└── deliverables/
    └── ai_interpreter_day1_pr_evidence_*.zip
```

## Demo 视频链接

待补充。

当前可复现证据是本地 runner 和 transcript 输出。正式提交前建议录制 1-3 分钟 demo，展示：

1. 打开 README。
2. 运行 mock 数据校验。
3. 运行 mock demo runner。
4. 打开 `transcript.md` 和 `transcript.json`。
5. 说明当前是 P0 mock proof chain，不是生产同传。

## PR 与 commit 规范说明

本分支建议作为 Day 1 的第一个 PR：

```text
PR 1: 初始化 AI 同声传译助手 Day 1 工程证据包
```

建议 PR 描述、commit 拆分和无效红线自检见：

```text
docs/ai_interpreter/05_day1_pr_commit_evidence.md
```

本次 PR 应保持“只做一件事”：初始化 Day 1 工程证据包。后续真实 ASR/LLM adapter、前端 UI、demo polish 都应拆成独立 PR。

## 已知限制

- 当前是 P0 mock proof chain，不是生产应用。
- 未接真实 ASR。
- 未接真实 LLM 或翻译模型。
- 未接真实会议平台。
- 未实现 TTS、多语种、API、数据库或前端。
- 未证明生产级低延迟。
- 如复用历史代码，必须在 PR 描述中注明来源。
- 如引入第三方依赖，必须在 README 和 PR 描述中列明。
