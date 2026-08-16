# Knowledge RAG — Evaluation Report

- Generated: 2026-08-16T12:58:44.986738+00:00
- Documents: aurora-labs.txt, data-privacy.md, faq.md, products.csv
- Settings: chunk_size=500, overlap=100, strategy=fixed, candidates=20, top_k=5, reranker=False
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.2875 |
| context_recall | 0.75 |
| recall_at_pool | 0.875 |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 80.4656 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Faithfulness | Answer rel. | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | How much does the Atlas analytics platform cost? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 181.49 |
| q2 | Which Aurora Labs product integrates with Slack? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 87.56 |
| q3 | What uptime SLA does Nimbus offer? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 66.94 |
| q4 | Where is Aurora Labs headquartered? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 89.08 |
| q5 | What security certifications does Aurora Labs hold? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 70.68 |
| q6 | How many employees work at Aurora Labs? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 77.63 |
| q7 | When was Aurora Labs founded? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 80.63 |
| q8 | Which investors led Aurora Labs' funding rounds? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 77.76 |
| q9 | What does the Atlas Pro plan add? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 72.28 |
| q10 | How long is workspace content retained after account deletion? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 76.62 |
| q11 | How quickly must Aurora Labs notify customers of a data breach? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 65.82 |
| q12 | Which companies are Aurora Labs subprocessors? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 70.23 |
| q13 | What is the API rate limit on standard plans? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 91.51 |
| q14 | What response time do enterprise support customers receive? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 54.55 |
| q15 | How long does the free trial last? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 57.36 |
| q16 | Does Aurora Labs encrypt customer data at rest? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 67.31 |
