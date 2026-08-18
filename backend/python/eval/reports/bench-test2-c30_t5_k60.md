# Knowledge RAG — Evaluation Report

- Generated: 2026-08-18T11:21:56.578674+00:00
- Documents: aurora-labs.pdf, aurora-labs.txt, data-privacy.md, faq.md, guide.docx, products.csv
- Settings: chunk_size=500, overlap=100, strategy=structure_aware, candidates=30, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.375 |
| context_recall | 0.7708 |
| recall_at_pool | 1.0 |
| structure_pass_rate | n/a |
| faithfulness | n/a |
| answer_relevance | n/a |
| declined_correctly | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 1201.7444 |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Structure | Faithfulness | Answer rel. | Declined | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | — | How much does the Atlas analytics platform cost? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 1324.31 |
| q2 | — | Which Aurora Labs product integrates with Slack? | 5 | 4 | 0.8 | 1.0 | 1.0 | — | n/a | n/a | — | 1212.01 |
| q3 | — | What uptime SLA does Nimbus offer? | 5 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 1175.33 |
| q4 | — | Where is Aurora Labs headquartered? | 5 | 3 | 0.6 | 0.75 | 1.0 | — | n/a | n/a | — | 1183.98 |
| q5 | — | What security certifications does Aurora Labs hold? | 5 | 3 | 0.6 | 0.75 | 1.0 | — | n/a | n/a | — | 1176.39 |
| q6 | — | How many employees work at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 1184.87 |
| q7 | — | When was Aurora Labs founded? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 1180.45 |
| q8 | — | Which investors led Aurora Labs' funding rounds? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 1197.79 |
| q9 | — | What does the Atlas Pro plan add? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 1206.51 |
| q10 | — | How long is workspace content retained after account deletion? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 1172.51 |
| q11 | — | How quickly must Aurora Labs notify customers of a data breach? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 1182.6 |
| q12 | — | Which companies are Aurora Labs subprocessors? | 5 | 0 | 0.0 | 0.0 | 1.0 | — | n/a | n/a | — | 1189.53 |
| q13 | — | What is the API rate limit on standard plans? | 5 | 1 | 0.2 | 0.5 | 1.0 | — | n/a | n/a | — | 1209.89 |
| q14 | — | What response time do enterprise support customers receive? | 5 | 2 | 0.4 | 0.6667 | 1.0 | — | n/a | n/a | — | 1219.32 |
| q15 | — | How long does the free trial last? | 5 | 4 | 0.8 | 0.6667 | 1.0 | — | n/a | n/a | — | 1198.6 |
| q16 | — | Does Aurora Labs encrypt customer data at rest? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 1213.82 |
