# Knowledge RAG — Evaluation Report

- Generated: 2026-08-18T11:22:25.481978+00:00
- Documents: aurora-labs.pdf, aurora-labs.txt, data-privacy.md, faq.md, guide.docx, products.csv
- Settings: chunk_size=500, overlap=100, strategy=structure_aware, candidates=50, top_k=3, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.5417 |
| context_recall | 0.7135 |
| recall_at_pool | 1.0 |
| structure_pass_rate | n/a |
| faithfulness | n/a |
| answer_relevance | n/a |
| declined_correctly | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 1388.2894 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Structure | Faithfulness | Answer rel. | Declined | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | — | How much does the Atlas analytics platform cost? | 3 | 2 | 0.6667 | 0.6667 | 1.0 | — | n/a | n/a | — | 1382.66 |
| q2 | — | Which Aurora Labs product integrates with Slack? | 3 | 3 | 1.0 | 0.75 | 1.0 | — | n/a | n/a | — | 1359.38 |
| q3 | — | What uptime SLA does Nimbus offer? | 3 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 1380.62 |
| q4 | — | Where is Aurora Labs headquartered? | 3 | 3 | 1.0 | 0.75 | 1.0 | — | n/a | n/a | — | 1330.29 |
| q5 | — | What security certifications does Aurora Labs hold? | 3 | 3 | 1.0 | 0.75 | 1.0 | — | n/a | n/a | — | 1330.58 |
| q6 | — | How many employees work at Aurora Labs? | 3 | 2 | 0.6667 | 1.0 | 1.0 | — | n/a | n/a | — | 1374.41 |
| q7 | — | When was Aurora Labs founded? | 3 | 2 | 0.6667 | 1.0 | 1.0 | — | n/a | n/a | — | 1374.74 |
| q8 | — | Which investors led Aurora Labs' funding rounds? | 3 | 2 | 0.6667 | 1.0 | 1.0 | — | n/a | n/a | — | 1437.37 |
| q9 | — | What does the Atlas Pro plan add? | 3 | 1 | 0.3333 | 1.0 | 1.0 | — | n/a | n/a | — | 1441.6 |
| q10 | — | How long is workspace content retained after account deletion? | 3 | 1 | 0.3333 | 1.0 | 1.0 | — | n/a | n/a | — | 1395.99 |
| q11 | — | How quickly must Aurora Labs notify customers of a data breach? | 3 | 1 | 0.3333 | 1.0 | 1.0 | — | n/a | n/a | — | 1385.49 |
| q12 | — | Which companies are Aurora Labs subprocessors? | 3 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 1351.03 |
| q13 | — | What is the API rate limit on standard plans? | 3 | 1 | 0.3333 | 0.5 | 1.0 | — | n/a | n/a | — | 1391.75 |
| q14 | — | What response time do enterprise support customers receive? | 3 | 2 | 0.6667 | 0.6667 | 1.0 | — | n/a | n/a | — | 1386.06 |
| q15 | — | How long does the free trial last? | 3 | 2 | 0.6667 | 0.3333 | 1.0 | — | n/a | n/a | — | 1360.27 |
| q16 | — | Does Aurora Labs encrypt customer data at rest? | 3 | 1 | 0.3333 | 1.0 | 1.0 | — | n/a | n/a | — | 1530.39 |
