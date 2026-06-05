# AI Interpreter Mock Transcript

## Summary
- Stream: Building a RAG Assistant with a Vector Database
- Stream ID: stream_tech_talk_p0_001
- Final segments: 10
- Glossary entries: 10
- Term hits: 13
- Optional revision demo exists: true

## Timeline

| Time | English | Chinese | Term Hits |
|---|---|---|---|
| 00:00-00:04 | Today we are building a RAG assistant for internal documentation. | 今天我们要构建一个面向内部文档的检索增强生成助手。 | RAG -> 检索增强生成 |
| 00:08-00:11 | The API receives a user question and creates an embedding for retrieval. | API 接收用户问题，并为检索创建一个嵌入向量。 | API -> API<br>embedding -> 嵌入向量 |
| 00:16-00:20 | We store the vectors in a vector database so similar documents can be found quickly. | 我们把向量存入向量数据库，以便快速找到相似文档。 | vector database -> 向量数据库 |
| 00:24-00:29 | Latency matters because the subtitle must stay close to the speaker's pace. | 延迟很重要，因为字幕必须尽量贴近讲者节奏。 | Latency -> 延迟 |
| 00:33-00:38 | A glossary keeps key terms such as RAG and embedding translated consistently. | 术语表让 RAG 和嵌入向量等关键术语保持一致译法。 | glossary -> 术语表<br>RAG -> 检索增强生成<br>embedding -> 嵌入向量 |
| 00:42-00:47 | The system marks partial text as unstable and commits only final segments to the timeline. | 系统把临时识别结果标记为不稳定，只把稳定识别结果提交到时间轴。 | partial -> 临时识别结果<br>final -> 稳定识别结果<br>timeline -> 时间轴 |
| 00:51-00:55 | If the translation model fails, the demo can fall back to a prepared translation. | 如果翻译模型失败，演示可以降级使用预置译文。 | - |
| 01:00-01:04 | The review timeline shows the English sentence, Chinese translation, and matched terms. | 复盘时间轴展示英文句子、中文翻译和命中的术语。 | timeline -> 时间轴 |
| 01:09-01:14 | At the end we export the bilingual transcript as Markdown and JSON. | 最后我们把双语 transcript 导出为 Markdown 和 JSON。 | Markdown -> Markdown |
| 01:19-01:24 | This mock stream proves the workflow before we connect any real ASR or meeting platform. | 这条 mock 流用于先证明工作流，再接入真实 ASR 或会议平台。 | - |

## Fallback Notes
- fallback_asr_prepared_stream: ASR unavailable. Using prepared partial/final event stream for this demo.
- fallback_translation_prepared_text: Translation adapter unavailable. Using prepared Chinese translations.
- fallback_export_copy_text: Export failed. Copyable bilingual timeline is available on the page.
- fallback_builtin_glossary: Term import failed. Built-in technical glossary is active.

P2 revision demo data is optional and is not included in the main timeline.
