# AI 同声传译助手项目交接说明

版本：v0.2  
交接范围：Planner/Executor 多轮调研、技术提案、架构设计、实现设计前置契约、MVP 分析。  
当前定位：面向英文技术分享和网课场景的 AI 同声传译助手，把“会前术语控制、会中稳定字幕、会后双语复盘”做成可验证闭环。

## 1. 交接结论

项目已经完成从研究基线到设计骨架的收敛，当前不再建议继续泛化调研。下一位同学应优先按 MVP 纵切做最小实现，而不是扩展会议平台、完整自动回修、多语种或复杂知识库。

当前四份正式文档：

| 文档 | 作用 | 当前状态 |
|---|---|---|
| `01_technical_proposal.md` | 技术提案，回答 Why / Whether | 已完成产品定位、痛点证据边界、MVP 范围、答辩口径。 |
| `02_architecture_design.md` | 架构设计，回答 System How | 已完成最小系统边界、模块职责、数据流、mock/real 替换边界。 |
| `03_implementation_design.md` | 实现设计，回答 Module How | 已收敛为实现前置契约：对象、事件、状态流转、验收样例。 |
| `04_mvp_analysis.md` | MVP 分析，回答 72 小时怎么交付 | 已完成范围裁剪、Day 0-Day 3 计划、评分点证据矩阵。 |

三类设计文档边界：

| 文档类型 | 回答问题 | 不做什么 |
|---|---|---|
| 技术提案 | 为什么做、为谁做、是否值得进入 MVP | 不写架构图、API、表结构、代码。 |
| 架构设计 | 系统整体怎么组织、模块边界和数据流如何协作 | 不写具体接口字段、数据库表、测试代码。 |
| 实现设计 | 模块落地前的对象、事件、状态和验收契约 | 当前不写代码、不绑定 API endpoint、不选技术栈。 |

## 2. 线程协作状态

本轮采用 Planner/Executor 双线程循环：

| 线程 | ID | 角色 | 最新状态 |
|---|---|---|---|
| Executor | `019e9412-84e3-7753-a46c-18685b0a2fc4` | 只执行 Planner 单任务 | Task 22 已完成并被接受；Task 23 由 Coordinator 兜底完成红队审查；当前执行 Task 24 最小修订。 |
| Planner | `019e941d-e960-70d1-a051-b10e13b43b8e` | 审查结果并发下一张任务卡 | 已接受 Task 22 和 Task 23 兜底审查；下一步是按红队清单修订过期状态和架构边界。 |

建议交接后第一步：

1. 快速复核 `00_project_handoff.md`、`02_architecture_design.md`、`04_mvp_analysis.md` 的边界修订。
2. 确认 Task 22 的 XEngineer/ZGC 收敛边界已同步：P0 只保留术语约束、字幕状态、时间轴、导出和 fallback。
3. 让 Planner 输出下一张任务卡，建议方向是“最小实现任务 1：准备 mock 数据”。

## 3. 产品定义

一句话：不是再做一个实时字幕壳，而是把技术场景最痛的术语准确、字幕稳定和会后复盘连成闭环。

目标用户：

| 用户 | 场景 | 核心痛点 |
|---|---|---|
| 开发者/技术从业者 | 英文技术分享、发布会、论文讲解 | API、模型名、缩写、代码词错译影响理解。 |
| 学生/跨语言学习者 | 英文网课、公开课、课程回放 | 字幕状态不稳、专业术语难跟、会后难复盘。 |
| 技术团队成员 | 跨语培训、评审、例会回放 | 会中跟不上，会后缺少可追溯双语资料。 |

P0 最小闭环：

```text
固定英文技术分享音频或模拟流
  -> 术语表/热词导入
  -> ASR partial/final 事件
  -> 中文翻译
  -> 术语命中
  -> 双语时间轴
  -> Markdown/JSON 导出
```

P2 可选：一条伪数据 `RevisionDemoEvent`，展示“因术语命中解释性修订”的方向。它不是主链路，不承诺完整实时自动回修。

## 4. 证据和痛点边界

证据分级：

| 等级 | 含义 | 使用方式 |
|---|---|---|
| O1 | 官方文档/公告/产品页 | 证明产品能力、市场方向或反证，不能直接当用户痛点。 |
| U1 | 公开用户原话 | 可作为用户痛点证据。 |
| U2 | 应用商店/产品评论 | 可作为用户体验证据。 |
| U3 | 官方社区/论坛用户帖 | 可作为较高质量用户痛点证据。 |
| S1/S2 | 二手文章、聚合榜单、营销文 | 只能辅助，不做核心论据。 |
| I | 工程推断 | 必须标注为推断。 |

痛点归并：

| 痛点 | 证据强度 | 文档写法 |
|---|---|---|
| 术语/专名错译 | 较强 | 可作为主痛点，支撑术语表/热词导入。 |
| 会后不可追溯/难复盘 | 较强 | 可作为主痛点，支撑双语时间轴和导出。 |
| 网课/技术分享不适配 | 中等 | 可作为目标场景机会，不写成国内强验证。 |
| 字幕延迟/不稳定 | 中等偏弱 | 作为体验指标，用 partial/final 状态解释，不承诺低延迟。 |
| 前文错误无法自动回修 | 弱但有差异化 | 只写 P2 假设/演示，不写 P0 主能力。 |

必须避免的夸大表达：

- 已经证明所有用户都需要实时自动回修。
- 本方案比 Zoom/Teams/Google Meet 翻译字幕全面更好。
- 已支持真实会议平台、生产级低延迟和完整多语种同传。

## 5. 竞品和来源地图

已形成的竞品层次：

| 层次 | 代表方向 | 当前用途 |
|---|---|---|
| 国外官方产品 | Zoom、Teams、Google Meet、Otter、DeepL、Chrome Live Caption | 定位已有字幕/翻译/纪要能力边界。 |
| 国内官方产品 | 腾讯会议、飞书妙记、通义听悟、QQ 浏览器实时字幕、有道类同传产品 | 证明中文侧已有能力和场景覆盖，但不能替代用户痛点证据。 |
| 公开用户社区 | Reddit、Hacker News、V2EX、官方课程社区 | 采集术语错译、字幕节奏、课程字幕适配、会后复盘问题。 |
| 开源/技术栈 | 仍待下一阶段细化 | 当前只保留 mock/real adapter 边界，不做选型承诺。 |

注意：开源技术栈还没有进入深度选型，不要在交接时宣称已完成 Whisper、Vosk、FunASR、WebRTC、字幕导出库等比较。

## 6. 架构边界

最小系统模块：

| 模块 | 责任 | 降级 |
|---|---|---|
| Demo Input / Sample Stream | 提供固定英文技术分享输入或模拟事件流 | 无音频时直接播放预置事件。 |
| ASR Event Adapter | 输出 partial/final 文本事件 | 真实 ASR 失败则切模拟事件。 |
| Subtitle State Manager | 管理 current 字幕和 final 入时间轴 | 只展示 final。 |
| Translation Adapter | final 英文转中文 | 翻译失败则使用预置译文。 |
| Term Glossary / Hotword Manager | 术语导入、匹配和命中 | 导入失败则使用内置术语表。 |
| Timeline Store | 保存 final 双语句段和术语命中 | 页面保留可复制时间轴。 |
| Exporter | 导出 Markdown/JSON | 文件导出失败则展示可复制文本。 |
| Demo UI | 展示导入、字幕、状态、时间轴、导出 | 简化为单页 demo。 |
| Fallback Controller | 控制 mock/real 切换和失败提示 | UI 必须显示降级原因。 |
| P2 Revision Demo | 可选解释性回修样例 | P0 未稳则砍掉。 |

mock/real 替换边界：ASR、翻译、术语表、时间轴、导出都可以先 mock，只要保持相同输入输出边界。真实引擎替换不能改变 P0 验收样例。

## 7. 实现契约

最小数据对象：

| 对象 | 用途 |
|---|---|
| `SampleStream` | 固定技术分享输入或模拟流。 |
| `ASREvent` | ASR partial/final 输出事件。 |
| `TermEntry` | 术语/热词条目。 |
| `TermHit` | 一次术语命中。 |
| `SubtitleSegment` | 字幕片段。 |
| `TranslationResult` | 翻译结果。 |
| `TimelineItem` | 会后复盘时间轴条目。 |
| `ExportArtifact` | Markdown/JSON 导出结果。 |
| `FallbackMode` | 降级模式和可见提示。 |
| `RevisionDemoEvent` | P2 optional 伪数据回修演示。 |

核心状态：

| 状态对象 | 流转 |
|---|---|
| ASR | `partial -> final` |
| 字幕 | `current -> timeline` |
| 翻译 | `pending -> ready -> fallback` |
| 导出 | `not_started -> generated -> fallback_copy` |
| 术语 | `loaded -> hit_detected -> rendered` |
| 降级 | `inactive -> active -> visible_notice` |
| P2 回修 | `not_used -> demo_triggered` |

实现暂时不定义：具体 API endpoint、数据库表结构、供应商 SDK、多用户权限、会议平台接入、完整实时自动回修 pipeline、PDF/SRT/VTT 全格式导出、生产级监控计费审计。

## 8. MVP 计划

72 小时拆分：

| 时间 | 目标 | 必须展示 |
|---|---|---|
| Day 0 | 冻结范围、准备样例、术语表、预期输出 | 有 8-12 句样例、至少 8 个术语、人工期望输出。 |
| Day 1 | 最小 UI、模拟 ASR、partial/final、final 入时间轴 | 页面能播放事件流并把 final 追加到时间轴。 |
| Day 2 | 翻译、术语命中、双语时间轴、Markdown/JSON 导出 | 每条 final 有中文，至少 5 个术语命中，可导出。 |
| Day 3 | 打磨、验收、降级预案、演示脚本 | 3 分钟跑通，ASR/翻译/导出失败时可降级。 |

P0 必过样例：

- `D0_SAMPLE_STREAM_READY`
- `D0_TERM_GLOSSARY_READY`
- `D0_EXPECTED_OUTPUT_READY`
- `D1_ASR_PARTIAL_FINAL_FLOW`
- `D1_CURRENT_SUBTITLE_VISIBLE`
- `D1_FINAL_SEGMENT_TO_TIMELINE`
- `D2_TRANSLATION_READY`
- `D2_TERM_HIT_HIGHLIGHT`
- `D2_BILINGUAL_TIMELINE_READY`
- `D2_EXPORT_MARKDOWN_JSON`
- `D3_FALLBACK_DEMO_READY`
- `D3_DEMO_SCRIPT_RUNTHROUGH`

P2 可砍：`D3_P2_REVISION_DEMO_OPTIONAL`。P0 任意一项不稳，直接砍掉。

## 9. 交付包检查清单

交付给评审或队友时，至少应包含：

- README：项目定位、MVP 范围、运行方式、核心能力、评分点映射、已知限制。
- Demo 输入：固定英文技术分享样例或模拟事件流。
- 术语表：至少 8 个技术术语，demo 中至少 5 个命中。
- Demo 主路径：导入术语、播放字幕、展示翻译、查看时间轴、导出 Markdown/JSON。
- 降级说明：ASR 失败、翻译失败、导出失败、术语导入失败时的 fallback。
- 截图/录屏：术语表、partial/final、双语字幕、时间轴、导出结果、fallback。
- 已知限制：真实会议平台、生产级低延迟、完整实时自动回修、多语种、多说话人、PDF/SRT/VTT、中文强证据都不承诺。

## 10. 下一步建议

建议下一位同学按这个顺序接手：

1. 先做一次红队审查：检查四份文档是否还有 API/DB/Revision/SRT/真实会议平台过度承诺。
2. 开始最小实现：先写 `SampleStream`、`TermEntry`、`ASREvent` mock 数据。
3. 跑通 `partial -> final -> timeline -> translation -> term_hit -> export`。
4. 再补导出预览、文件下载和 fallback 演示。
5. 最后才考虑真实 ASR、真实翻译和 P2 回修 demo。

不要优先做：会议平台插件、浏览器音频捕获、完整自动回修、多用户权限、SRT/PDF 全导出、大规模竞品报告。
