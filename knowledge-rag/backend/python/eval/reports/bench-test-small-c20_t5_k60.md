# Knowledge RAG — Evaluation Report

- Generated: 2026-08-18T11:18:29.743560+00:00
- Documents: aurora-labs.pdf, aurora-labs.txt, data-privacy.md, faq.md, guide.docx, products.csv
- Settings: chunk_size=500, overlap=100, strategy=structure_aware, candidates=20, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.375 |
| context_recall | 0.7708 |
| recall_at_pool | 0.9844 |
| structure_pass_rate | n/a |
| faithfulness | n/a |
| answer_relevance | n/a |
| declined_correctly | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 1393.6294 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Structure | Faithfulness | Answer rel. | Declined | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | — | How much does the Atlas analytics platform cost? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 10051.39 |
| q2 | — | Which Aurora Labs product integrates with Slack? | 5 | 4 | 0.8 | 1.0 | 1.0 | — | n/a | n/a | — | 807.56 |
| q3 | — | What uptime SLA does Nimbus offer? | 5 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 826.03 |
| q4 | — | Where is Aurora Labs headquartered? | 5 | 3 | 0.6 | 0.75 | 0.75 | — | n/a | n/a | — | 836.07 |
| q5 | — | What security certifications does Aurora Labs hold? | 5 | 3 | 0.6 | 0.75 | 1.0 | — | n/a | n/a | — | 779.83 |
| q6 | — | How many employees work at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 794.89 |
| q7 | — | When was Aurora Labs founded? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 913.58 |
| q8 | — | Which investors led Aurora Labs' funding rounds? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 846.12 |
| q9 | — | What does the Atlas Pro plan add? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 806.69 |
| q10 | — | How long is workspace content retained after account deletion? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 823.24 |
| q11 | — | How quickly must Aurora Labs notify customers of a data breach? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 806.1 |
| q12 | — | Which companies are Aurora Labs subprocessors? | 5 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 808.1 |
| q13 | — | What is the API rate limit on standard plans? | 5 | 1 | 0.2 | 0.5 | 1.0 | — | n/a | n/a | — | 813.44 |
| q14 | — | What response time do enterprise support customers receive? | 5 | 2 | 0.4 | 0.6667 | 1.0 | — | n/a | n/a | — | 791.78 |
| q15 | — | How long does the free trial last? | 5 | 4 | 0.8 | 0.6667 | 1.0 | — | n/a | n/a | — | 800.99 |
| q16 | — | Does Aurora Labs encrypt customer data at rest? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 792.26 |
