# Knowledge RAG — Evaluation Report

- Generated: 2026-08-16T13:02:03.317488+00:00
- Documents: aurora-labs.txt, data-privacy.md, faq.md, products.csv
- Settings: chunk_size=500, overlap=100, strategy=structure_aware, candidates=20, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.3125 |
| context_recall | 0.8625 |
| recall_at_pool | 0.9375 |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 1296.7487 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Faithfulness | Answer rel. | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | How much does the Atlas analytics platform cost? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 7869.41 |
| q2 | Which Aurora Labs product integrates with Slack? | 5 | 4 | 0.8 | 1.0 | 1.0 | n/a | n/a | 895.84 |
| q3 | What uptime SLA does Nimbus offer? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 853.52 |
| q4 | Where is Aurora Labs headquartered? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 850.97 |
| q5 | What security certifications does Aurora Labs hold? | 5 | 4 | 0.8 | 0.8 | 1.0 | n/a | n/a | 830.65 |
| q6 | How many employees work at Aurora Labs? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 823.93 |
| q7 | When was Aurora Labs founded? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 826.05 |
| q8 | Which investors led Aurora Labs' funding rounds? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 852.04 |
| q9 | What does the Atlas Pro plan add? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 833.76 |
| q10 | How long is workspace content retained after account deletion? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 844.58 |
| q11 | How quickly must Aurora Labs notify customers of a data breach? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 842.26 |
| q12 | Which companies are Aurora Labs subprocessors? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 842.64 |
| q13 | What is the API rate limit on standard plans? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 1013.94 |
| q14 | What response time do enterprise support customers receive? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 877.56 |
| q15 | How long does the free trial last? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 840.0 |
| q16 | Does Aurora Labs encrypt customer data at rest? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 850.83 |
