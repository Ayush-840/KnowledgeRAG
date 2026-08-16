# Knowledge RAG — Evaluation Report

- Generated: 2026-08-16T15:00:21.363793+00:00
- Documents: api-reference.md, atlas-product-sheet.pdf, benefits-faq.md, employee-handbook-v1.md, employee-handbook-v2.md, feature-comparison.md, gdpr-faq.md, incident-runbook.txt, oncall-handbook.md, platform-report-part1.md, platform-report-part2.md, privacy-policy-v1.md, privacy-policy-v2.md, product-pricing.csv, security-policy.docx, sla-agreement.md, vendor-contract-v2.md, vendor-contract.md
- Settings: chunk_size=500, overlap=100, strategy=fixed, candidates=20, top_k=5, reranker=False
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.2583 |
| context_recall | 0.7709 |
| recall_at_pool | 0.8597 |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 51.9289 |

### By query type

| Type | n | Precision | Recall | Recall@pool | Faithfulness | Ans. rel. |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous | 12 | 0.2167 | 0.8889 | 0.9167 | n/a | n/a |
| multi_hop | 19 | 0.4421 | 0.7723 | 0.9419 | n/a | n/a |
| single_hop | 36 | 0.2111 | 0.838 | 0.9167 | n/a | n/a |
| unanswerable | 5 | 0.0 | 0.0 | 0.0 | n/a | n/a |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Faithfulness | Answer rel. | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q001 | single_hop | How much does Atlas Standard cost per user per month? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 14.23 |
| q002 | single_hop | What monthly uptime guarantee does Beacon offer under the SLA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 21.92 |
| q003 | single_hop | What is the p95 warm query latency of the Calcite query engine? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 14.78 |
| q004 | single_hop | What percentage does Aurora Labs match on employee 401(k) contributions? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 20.33 |
| q005 | single_hop | How quickly must an on-call engineer acknowledge a SEV1 page? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 22.09 |
| q006 | single_hop | What is the SKU of the Atlas analytics platform? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 15.59 |
| q007 | single_hop | What is the annual fee Acme Corp pays under the current Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 24.52 |
| q008 | single_hop | Which Aurora Labs product is the alerting and monitoring service? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 22.85 |
| q009 | single_hop | What is the base URL of the Aurora Labs REST API? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 14.74 |
| q010 | single_hop | How long is the probation period for new hires at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 12.63 |
| q011 | single_hop | How many named users does Acme Corp get under the current MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 9.63 |
| q012 | single_hop | What is the codename of the stream processor behind Nimbus? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 9.86 |
| q013 | single_hop | How many chart types does the Atlas dashboard builder support? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 11.25 |
| q014 | single_hop | What is the Nimbus Enterprise monthly uptime guarantee? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 12.45 |
| q015 | single_hop | What is the API rate limit for the free tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 10.69 |
| q016 | single_hop | How long after an incident must the post-incident review be completed? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 8.36 |
| q017 | single_hop | What is the wellness stipend amount per month? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 7.22 |
| q018 | single_hop | Which codename is used for the Aurora Labs catalog service? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 10.94 |
| q019 | single_hop | How often must API keys be rotated according to the security policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 54.66 |
| q020 | single_hop | What is the p95 write latency of the Marina catalog service? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 31.53 |
| q021 | single_hop | What is the learning budget per employee per year? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 167.9 |
| q022 | single_hop | Who is Aurora Labs' EU representative under GDPR? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 47.2 |
| q023 | single_hop | What is the p95 end-to-end processing latency of Kestrel? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 43.02 |
| q024 | single_hop | What is the initial term of the current Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 42.4 |
| q025 | multi_hop | Which product does the Calcite query engine power, and what is its warm p95 latency? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 43.58 |
| q026 | multi_hop | What happens when Nimbus pipeline lag exceeds 30 minutes, and what does the SLA commit for pipeline lag? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 80.62 |
| q027 | multi_hop | What uptime guarantee does the product behind Beacon offer, and what pricing tier is available? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 43.56 |
| q028 | multi_hop | What is the retention period in the version of the privacy policy that supersedes Version 1? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 40.55 |
| q029 | multi_hop | Which service does the incident runbook say powers the data pipeline, and what is its throughput ceiling per the benchmark report? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 28.21 |
| q030 | multi_hop | What does the current employee handbook say about parental leave, and what additional weeks does the benefits FAQ mention? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 55.6 |
| q031 | multi_hop | Which data sources can Atlas connect to, and what does the Atlas Enterprise edition cost? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 43.26 |
| q032 | multi_hop | What is the SEV2 response time in the runbook, and what is the SLA credit percentage for Beacon? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 38.94 |
| q033 | multi_hop | How much does the Nimbus Enterprise tier cost, and what uptime guarantee does it receive? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 47.85 |
| q034 | multi_hop | What is the maximum catalog size tested for Marina, and which codename is the query engine? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 122.35 |
| q035 | multi_hop | What encryption does the privacy policy promise at rest, and what does the security policy require for restricted data? | 5 | 3 | 0.6 | 0.6 | 0.8 | n/a | n/a | 58.03 |
| q036 | multi_hop | Which product integrates with Slack, and how much does its Standard tier cost? | 5 | 5 | 1.0 | 0.25 | 0.8 | n/a | n/a | 38.71 |
| q037 | multi_hop | What is the equity vesting schedule in the employee handbook, and what is the 401(k) match percentage? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 61.75 |
| q038 | multi_hop | How long does the runbook say an incident can run before escalating to the VP of Engineering, and what is the SLA's Nimbus lag commitment? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 99.47 |
| q039 | multi_hop | Which two data sources can Atlas and Nimbus both write to according to the feature comparison? | 5 | 1 | 0.2 | 0.25 | 1.0 | n/a | n/a | 26.93 |
| q040 | multi_hop | What is the backpressure onset lag measured for Kestrel, and which Kafka-based product does it power? | 5 | 4 | 0.8 | 0.1739 | 0.6957 | n/a | n/a | 38.26 |
| q041 | ambiguous | What is the current data retention period in the Aurora Labs privacy policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 43.2 |
| q042 | ambiguous | How many PTO days do employees get per year? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 52.44 |
| q043 | ambiguous | What is the renewal term in the Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 43.66 |
| q044 | ambiguous | What does Atlas cost? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 827.84 |
| q045 | ambiguous | What is the uptime guarantee for the Nimbus pipeline? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 44.61 |
| q046 | ambiguous | What encryption does Aurora Labs use for data at rest? | 5 | 2 | 0.4 | 0.6667 | 1.0 | n/a | n/a | 30.0 |
| q047 | ambiguous | What happens to customer content after the subscription term ends? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 36.42 |
| q048 | ambiguous | What is the p95 query latency target for Atlas? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 59.08 |
| q049 | ambiguous | Which document describes how to respond to a SEV1 incident? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 41.25 |
| q050 | ambiguous | What happens when an incident lasts more than 4 hours? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 37.52 |
| q051 | ambiguous | What is the Nimbus pipeline lag commitment? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 53.52 |
| q052 | ambiguous | How many PTO days carry over into the next year? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 53.11 |
| q053 | unanswerable | What is Aurora Labs' revenue for fiscal year 2024? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 17.14 |
| q054 | unanswerable | What is the email address of Aurora Labs' CEO? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 66.05 |
| q055 | unanswerable | What is the interest rate on Aurora Labs' line of credit? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 48.68 |
| q056 | unanswerable | How many employees does Aurora Labs have in Tokyo? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 39.04 |
| q057 | unanswerable | What is the version number of the Aurora mobile app? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 50.48 |
| q058 | single_hop | What is the maximum number of concurrent queries Calcite sustained in the benchmark? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 44.0 |
| q059 | single_hop | What is the Nimbus Free tier price? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 62.53 |
| q060 | single_hop | How long does Aurora Labs respond to a verified data subject access request? | 5 | 4 | 0.8 | 0.6667 | 1.0 | n/a | n/a | 36.31 |
| q061 | single_hop | What is the p95 write latency of Marina? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 37.43 |
| q062 | single_hop | What is the monthly uptime guarantee for Atlas analytics? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 44.31 |
| q063 | single_hop | How long are Aurora Labs usage telemetry records retained under the current policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 56.67 |
| q064 | single_hop | What is the health insurance premium coverage for employee dependents? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 50.86 |
| q065 | single_hop | Which error code does the API return for rate limit exceeded? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 58.24 |
| q066 | single_hop | What is the standard Nimbus monthly price for the Standard tier? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 34.68 |
| q067 | single_hop | How many weeks of paid parental leave do new parents receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 44.03 |
| q068 | single_hop | What is the liability cap in the current Acme MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 36.62 |
| q069 | single_hop | How many production regions does the Aurora Labs platform run in? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 37.95 |
| q070 | multi_hop | What is the Beacon delivery delay limit in the runbook, and what uptime guarantee does Beacon carry in the SLA? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 42.28 |
| q071 | multi_hop | What does the runbook say to check when Atlas query timeouts occur, and what is the SLA latency target for Atlas? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 29.87 |
| q072 | multi_hop | Which regions host customer data per the GDPR FAQ, and what is the retention period for usage telemetry in the current privacy policy? | 5 | 2 | 0.4 | 0.4 | 0.6 | n/a | n/a | 60.6 |
