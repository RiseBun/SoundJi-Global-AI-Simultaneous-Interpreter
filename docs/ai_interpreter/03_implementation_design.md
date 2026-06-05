# AI 同声传译助手实现设计

版本：v0.2

本文档属于实现设计，回答的是：模块具体落地前，需要先锁定哪些对象、事件、状态流转和验收样例。当前版本是实现设计前置契约，不写代码，不写具体接口端点，不写数据库表结构，不绑定技术栈。

本文承接技术提案和架构设计：

- 不重新论证项目为什么值得做。
- 不改变架构设计中的最小系统边界。
- 不新增产品范围。
- 不把 P2 自动回修写入 P0 主链路。
- 不定义会议平台接入、多用户权限、生产级监控或完整导出生态。

## 1. 实现边界

P0 主链路只覆盖：

```text
SampleStream
  -> ASREvent partial/final
  -> SubtitleSegment current/timeline
  -> TranslationResult
  -> TermHit
  -> TimelineItem
  -> ExportArtifact Markdown/JSON
  -> FallbackMode visible notice
```

P2 optional 只允许存在一个 `RevisionDemoEvent`，用于展示伪数据回修方向。它不是实时自动回修系统，也不能阻塞 P0 演示。

## 2. 最小数据对象契约

| 对象 | 用途 | 关键字段名 | 生产模块 | 消费模块 | 验收样例 |
|---|---|---|---|---|---|
| `SampleStream` | 表示固定技术分享输入或模拟流 | `stream_id`, `title`, `mode`, `events`, `duration_ms` | Demo Input / Sample Stream | ASR Event Adapter, Demo UI | `D0_SAMPLE_STREAM_READY` |
| `ASREvent` | 表示 ASR 输出事件 | `event_id`, `stream_id`, `ts_ms`, `text`, `status`, `sequence` | ASR Event Adapter | Subtitle State Manager | `D1_ASR_PARTIAL_FINAL_FLOW` |
| `TermEntry` | 表示术语/热词条目 | `term_id`, `source_text`, `target_text`, `aliases`, `category` | Term Glossary / Hotword Manager | Translation Adapter, Subtitle State Manager | `D0_TERM_GLOSSARY_READY` |
| `TermHit` | 表示一次术语命中 | `hit_id`, `term_id`, `segment_id`, `source_text`, `target_text`, `position` | Term Glossary / Hotword Manager | Demo UI, Timeline Store, Exporter | `D2_TERM_HIT_HIGHLIGHT` |
| `SubtitleSegment` | 表示字幕片段 | `segment_id`, `stream_id`, `start_ms`, `end_ms`, `source_text`, `status` | Subtitle State Manager | Translation Adapter, Timeline Store, Demo UI | `D1_FINAL_SEGMENT_TO_TIMELINE` |
| `TranslationResult` | 表示翻译结果 | `translation_id`, `segment_id`, `target_text`, `status`, `used_terms` | Translation Adapter | Subtitle State Manager, Timeline Store, Demo UI | `D2_TRANSLATION_READY` |
| `TimelineItem` | 表示会后复盘时间轴条目 | `item_id`, `segment_id`, `start_ms`, `end_ms`, `source_text`, `target_text`, `term_hits` | Timeline Store | Demo UI, Exporter | `D2_BILINGUAL_TIMELINE_READY` |
| `ExportArtifact` | 表示导出结果 | `artifact_id`, `format`, `content`, `status`, `created_at` | Exporter | Demo UI, Fallback Controller | `D2_EXPORT_MARKDOWN_JSON` |
| `FallbackMode` | 表示降级模式 | `mode_id`, `reason`, `active`, `fallback_source`, `visible_notice` | Fallback Controller | Demo UI, ASR Event Adapter, Translation Adapter, Exporter | `D3_FALLBACK_DEMO_READY` |
| `RevisionDemoEvent` | P2 optional，仅表示伪数据回修演示 | `revision_id`, `segment_id`, `before_text`, `after_text`, `reason`, `is_demo_only` | P2 Revision Demo | Demo UI, Exporter | `D3_P2_REVISION_DEMO_OPTIONAL` |

## 3. 最小事件类型

| 事件类型 | 说明 | 优先级 |
|---|---|---|
| `stream_started` | 开始播放固定输入或模拟流 | P0 |
| `asr_partial_received` | 收到 partial 文本 | P0/P1 |
| `asr_final_received` | 收到 final 文本 | P0 |
| `subtitle_current_updated` | 当前字幕区更新 | P0 |
| `segment_committed_to_timeline` | final 句子写入时间轴 | P0 |
| `translation_pending` | final 句子进入翻译等待 | P0 |
| `translation_ready` | 中文译文可展示 | P0 |
| `translation_fallback_used` | 使用预置译文 | P0 |
| `terms_loaded` | 术语表加载完成 | P0 |
| `term_hit_detected` | 术语命中 | P0 |
| `export_requested` | 用户触发导出 | P0 |
| `export_generated` | Markdown/JSON 生成 | P0 |
| `export_fallback_copy_ready` | 文件导出失败，提供可复制文本 | P0 |
| `fallback_mode_activated` | ASR/翻译/导出降级启动 | P0 |
| `revision_demo_triggered` | P2 伪数据回修演示触发 | P2 optional |

## 4. 状态流转

| 状态对象 | 流转 | 验收点 |
|---|---|---|
| ASR | `partial -> final` | partial 可显示，final 固定进入时间轴。 |
| 字幕 | `current -> timeline` | current 可被更新；final 后不再覆盖，进入 timeline。 |
| 翻译 | `pending -> ready -> fallback` | ready 展示译文；失败时 fallback 使用预置译文。 |
| 导出 | `not_started -> generated -> fallback_copy` | generated 输出 Markdown/JSON；失败时显示可复制文本。 |
| 术语 | `loaded -> hit_detected -> rendered` | 术语表加载后，命中可高亮或标注。 |
| 降级 | `inactive -> active -> visible_notice` | 降级必须在 UI 可见，不隐藏 mock 边界。 |
| P2 回修 | `not_used -> demo_triggered` | 只在 Day 3 可选演示，不进主链路。 |

## 5. 验收样例清单

| 样例名 | 对应阶段 | 验收目标 |
|---|---|---|
| `D0_SAMPLE_STREAM_READY` | Day 0 | 固定输入或模拟事件准备完成，包含 8-12 句技术内容。 |
| `D0_TERM_GLOSSARY_READY` | Day 0 | 术语表准备完成，至少包含 8 个术语。 |
| `D0_EXPECTED_OUTPUT_READY` | Day 0 | 预期输出样例可人工对照。 |
| `D1_ASR_PARTIAL_FINAL_FLOW` | Day 1 | 事件流能展示 partial 到 final。 |
| `D1_CURRENT_SUBTITLE_VISIBLE` | Day 1 | 当前字幕区域可随事件更新。 |
| `D1_FINAL_SEGMENT_TO_TIMELINE` | Day 1 | final 字幕固定写入时间轴。 |
| `D2_TRANSLATION_READY` | Day 2 | 每条 final 字幕有中文译文。 |
| `D2_TERM_HIT_HIGHLIGHT` | Day 2 | 至少 5 个术语命中可见。 |
| `D2_BILINGUAL_TIMELINE_READY` | Day 2 | 时间轴包含时间、英文、中文和术语命中。 |
| `D2_EXPORT_MARKDOWN_JSON` | Day 2 | 可导出 Markdown/JSON，或提供可复制文本。 |
| `D3_FALLBACK_DEMO_READY` | Day 3 | ASR/翻译/导出失败时能切换预置数据并显示降级说明。 |
| `D3_DEMO_SCRIPT_RUNTHROUGH` | Day 3 | 3 分钟内跑完从输入到导出的演示主路径。 |
| `D3_P2_REVISION_DEMO_OPTIONAL` | Day 3 | 可选展示一条伪数据回修样例，明确标注为 demo。 |

## 6. 最小验收样例表

| 验收样例 | 输入 | 操作 | 期望输出 | 失败降级 | 对应对象/事件 | 优先级 |
|---|---|---|---|---|---|---|
| `D0_SAMPLE_STREAM_READY` | 8-12 句英文技术分享文本或模拟音频 | 加载样例输入 | 生成可播放 `SampleStream` | ASR 失败时直接使用预置事件流 | `SampleStream`, `stream_started` | P0 |
| `D0_TERM_GLOSSARY_READY` | 术语表：RAG/API/vector database/embedding 等 | 导入或加载术语表 | `TermEntry` 列表可见 | 术语导入失败 -> 内置术语表 | `TermEntry`, `terms_loaded` | P0 |
| `D0_EXPECTED_OUTPUT_READY` | 样例输入和术语表 | 人工准备期望输出 | 至少 5 句有预期译文和术语命中 | 只验 5 句关键样例 | `TermEntry`, `TranslationResult`, `TermHit` | P0 |
| `D1_ASR_PARTIAL_FINAL_FLOW` | `SampleStream` 或预置 ASR 事件 | 点击开始播放 | 依次产生 `partial -> final` | ASR 失败 -> 预置事件流 | `ASREvent`, `asr_partial_received`, `asr_final_received` | P0 |
| `D1_CURRENT_SUBTITLE_VISIBLE` | partial/final ASR 事件 | 观察字幕区 | current 字幕随事件更新 | 只展示 final 字幕 | `SubtitleSegment`, `subtitle_current_updated` | P0 |
| `D1_FINAL_SEGMENT_TO_TIMELINE` | final ASR 事件 | 等待 final 生成 | final 句子追加到 timeline，不被后续 partial 覆盖 | 只追加英文 final | `SubtitleSegment`, `TimelineItem`, `segment_committed_to_timeline` | P0 |
| `D2_TRANSLATION_READY` | final 英文句子 | 触发翻译 | 中文译文 ready 并显示 | 翻译失败 -> 预置译文 | `TranslationResult`, `translation_pending`, `translation_ready`, `translation_fallback_used` | P0 |
| `D2_TERM_HIT_HIGHLIGHT` | final 文本、译文、术语表 | 运行术语匹配 | 至少 5 个术语命中并高亮或标注 | 只显示命中列表，不高亮 | `TermHit`, `term_hit_detected` | P0 |
| `D2_BILINGUAL_TIMELINE_READY` | final 英文、中文译文、术语命中 | 查看时间轴 | 每条 `TimelineItem` 含时间、英文、中文、术语命中 | 不含精确时间戳，仅保留顺序 | `TimelineItem`, `segment_committed_to_timeline` | P0 |
| `D2_EXPORT_MARKDOWN_JSON` | 双语时间轴 | 点击导出 | 生成 Markdown 或 JSON `ExportArtifact` | 导出失败 -> 页面可复制文本 | `ExportArtifact`, `export_requested`, `export_generated`, `export_fallback_copy_ready` | P0 |
| `D3_FALLBACK_DEMO_READY` | 模拟 ASR/翻译/导出失败 | 切换或触发 fallback | UI 显示降级原因并继续 demo | 全程使用预置事件流和预置译文 | `FallbackMode`, `fallback_mode_activated` | P0 |
| `D3_DEMO_SCRIPT_RUNTHROUGH` | 完整样例、术语表、预置降级 | 按 8 步脚本演示 | 3 分钟内从加载术语到导出跑通 | 缩短为 5 步，仅展示 P0 | `SampleStream`, `TimelineItem`, `ExportArtifact` | P0 |
| `D3_P2_REVISION_DEMO_OPTIONAL` | 一条伪数据回修样例 | 手动触发 P2 演示 | 展示 before/after/reason，并标注非主链路 | 砍掉或口头说明 | `RevisionDemoEvent`, `revision_demo_triggered` | P2 optional |

P0 必过样例：`D0_SAMPLE_STREAM_READY`、`D0_TERM_GLOSSARY_READY`、`D0_EXPECTED_OUTPUT_READY`、`D1_ASR_PARTIAL_FINAL_FLOW`、`D1_CURRENT_SUBTITLE_VISIBLE`、`D1_FINAL_SEGMENT_TO_TIMELINE`、`D2_TRANSLATION_READY`、`D2_TERM_HIT_HIGHLIGHT`、`D2_BILINGUAL_TIMELINE_READY`、`D2_EXPORT_MARKDOWN_JSON`、`D3_FALLBACK_DEMO_READY`、`D3_DEMO_SCRIPT_RUNTHROUGH`。

P1/P2 可砍样例：`D3_P2_REVISION_DEMO_OPTIONAL`、复杂术语高亮 UI、精确时间戳、文件下载优化。P0 未稳时全部砍掉。

Day 0 对应输入和术语准备；Day 1 对应 ASR 事件和字幕状态；Day 2 对应翻译、术语命中、时间轴和导出；Day 3 对应降级预案、演示脚本和可选 P2 demo。

## 7. 故意不定义

为避免 72 小时 MVP 过度设计，当前版本故意不定义：

- 具体接口端点和请求响应 schema。
- 数据库表结构、索引、迁移方案。
- ASR/翻译具体供应商和 SDK。
- 多用户、权限、登录、团队词库。
- Zoom、Teams、Google Meet 等会议平台接入。
- 完整实时自动回修 pipeline。
- PDF/SRT/VTT 等完整导出格式。
- 生产级监控、计费、审计系统。

## 8. 下一步实现顺序

1. 固定 `SampleStream` 和 `TermEntry` 样例。
2. 用 mock 事件跑通 `ASREvent partial -> final`。
3. 让 final `SubtitleSegment` 进入 `TimelineItem`。
4. 接入 `TranslationResult` 的 mock 或预置译文。
5. 接入 `TermHit` 高亮和导出标注。
6. 生成 Markdown/JSON `ExportArtifact`。
7. 加入 `FallbackMode` 可见提示。
8. 仅在 P0 稳定后考虑 `RevisionDemoEvent`。
