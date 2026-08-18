# Knowledge RAG — Evaluation Report

- Generated: 2026-08-16T16:57:07.645064+00:00
- Documents: aurora-labs.pdf, aurora-labs.txt, data-privacy.md, faq.md, guide.docx, products.csv
- Settings: chunk_size=500, overlap=100, strategy=fixed, candidates=20, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.425 |
| context_recall | 0.8594 |
| recall_at_pool | 1.0 |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 1053.7394 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Faithfulness | Answer rel. | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | — | How much does the Atlas analytics platform cost? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 7898.48 |
| q2 | — | Which Aurora Labs product integrates with Slack? | 5 | 4 | 0.8 | 1.0 | 1.0 | n/a | n/a | 598.47 |
| q3 | — | What uptime SLA does Nimbus offer? | 5 | 2 | 0.4 | 0.5 | 1.0 | n/a | n/a | 600.43 |
| q4 | — | Where is Aurora Labs headquartered? | 5 | 4 | 0.8 | 1.0 | 1.0 | n/a | n/a | 609.82 |
| q5 | — | What security certifications does Aurora Labs hold? | 5 | 4 | 0.8 | 1.0 | 1.0 | n/a | n/a | 588.46 |
| q6 | — | How many employees work at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 593.73 |
| q7 | — | When was Aurora Labs founded? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 590.23 |
| q8 | — | Which investors led Aurora Labs' funding rounds? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 605.68 |
| q9 | — | What does the Atlas Pro plan add? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 584.23 |
| q10 | — | How long is workspace content retained after account deletion? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 599.47 |
| q11 | — | How quickly must Aurora Labs notify customers of a data breach? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 597.26 |
| q12 | — | Which companies are Aurora Labs subprocessors? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 610.96 |
| q13 | — | What is the API rate limit on standard plans? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 603.66 |
| q14 | — | What response time do enterprise support customers receive? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 592.79 |
| q15 | — | How long does the free trial last? | 5 | 3 | 0.6 | 0.5 | 1.0 | n/a | n/a | 583.99 |
| q16 | — | Does Aurora Labs encrypt customer data at rest? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 602.17 |
