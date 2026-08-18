# Knowledge RAG — Evaluation Report

- Generated: 2026-08-18T11:17:04.210163+00:00
- Documents: api-reference.md, atlas-product-sheet.pdf, benefits-faq.md, employee-handbook-v1.md, employee-handbook-v2.md, feature-comparison.md, gdpr-faq.md, incident-runbook.txt, oncall-handbook.md, platform-report-part1.md, platform-report-part2.md, privacy-policy-v1.md, privacy-policy-v2.md, product-pricing.csv, security-policy.docx, sla-agreement.md, vendor-contract-v2.md, vendor-contract.md
- Settings: chunk_size=500, overlap=100, strategy=structure_aware, candidates=20, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.3313 |
| context_recall | 0.8077 |
| recall_at_pool | 0.8301 |
| structure_pass_rate | n/a |
| faithfulness | n/a |
| answer_relevance | n/a |
| declined_correctly | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 722.2865 |

### By query type

| Type | n | Precision | Recall | Recall@pool | Structure | Faithfulness | Ans. rel. | Declined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ambiguous | 12 | 0.1833 | 0.8333 | 0.8333 | n/a | n/a | n/a | n/a |
| multi_hop | 19 | 0.4947 | 0.6086 | 0.6745 | n/a | n/a | n/a | n/a |
| single_hop | 36 | 0.2944 | 0.9042 | 0.9112 | n/a | n/a | n/a | n/a |
| unanswerable | 5 | 0.0 | 0.0 | 0.0 | n/a | n/a | n/a | n/a |

### Generation (LLM-as-judge)

| Metric | Mean |
| --- | --- |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |

## Per query

| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Structure | Faithfulness | Answer rel. | Declined | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q001 | single_hop | How much does Atlas Standard cost per user per month? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 7698.8 |
| q002 | single_hop | What monthly uptime guarantee does Beacon offer under the SLA? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 384.18 |
| q003 | single_hop | What is the p95 warm query latency of the Calcite query engine? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 812.05 |
| q004 | single_hop | What percentage does Aurora Labs match on employee 401(k) contributions? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 374.08 |
| q005 | single_hop | How quickly must an on-call engineer acknowledge a SEV1 page? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 825.33 |
| q006 | single_hop | What is the SKU of the Atlas analytics platform? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 794.16 |
| q007 | single_hop | What is the annual fee Acme Corp pays under the current Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 779.97 |
| q008 | single_hop | Which Aurora Labs product is the alerting and monitoring service? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 821.02 |
| q009 | single_hop | What is the base URL of the Aurora Labs REST API? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 337.92 |
| q010 | single_hop | How long is the probation period for new hires at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 274.66 |
| q011 | single_hop | How many named users does Acme Corp get under the current MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 811.78 |
| q012 | single_hop | What is the codename of the stream processor behind Nimbus? | 5 | 2 | 0.4 | 0.1818 | 0.1818 | — | n/a | n/a | — | 782.93 |
| q013 | single_hop | How many chart types does the Atlas dashboard builder support? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 831.46 |
| q014 | single_hop | What is the Nimbus Enterprise monthly uptime guarantee? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 847.12 |
| q015 | single_hop | What is the API rate limit for the free tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 823.03 |
| q016 | single_hop | How long after an incident must the post-incident review be completed? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 811.0 |
| q017 | single_hop | What is the wellness stipend amount per month? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 804.87 |
| q018 | single_hop | Which codename is used for the Aurora Labs catalog service? | 5 | 1 | 0.2 | 0.0625 | 0.3125 | — | n/a | n/a | — | 535.69 |
| q019 | single_hop | How often must API keys be rotated according to the security policy? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 398.28 |
| q020 | single_hop | What is the p95 write latency of the Marina catalog service? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 804.35 |
| q021 | single_hop | What is the learning budget per employee per year? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 788.84 |
| q022 | single_hop | Who is Aurora Labs' EU representative under GDPR? | 5 | 4 | 0.8 | 1.0 | 1.0 | — | n/a | n/a | — | 324.18 |
| q023 | single_hop | What is the p95 end-to-end processing latency of Kestrel? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 831.95 |
| q024 | single_hop | What is the initial term of the current Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 838.74 |
| q025 | multi_hop | Which product does the Calcite query engine power, and what is its warm p95 latency? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 707.94 |
| q026 | multi_hop | What happens when Nimbus pipeline lag exceeds 30 minutes, and what does the SLA commit for pipeline lag? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 789.69 |
| q027 | multi_hop | What uptime guarantee does the product behind Beacon offer, and what pricing tier is available? | 5 | 2 | 0.4 | 0.6667 | 0.6667 | — | n/a | n/a | — | 456.78 |
| q028 | multi_hop | What is the retention period in the version of the privacy policy that supersedes Version 1? | 5 | 2 | 0.4 | 0.6667 | 1.0 | — | n/a | n/a | — | 299.95 |
| q029 | multi_hop | Which service does the incident runbook say powers the data pipeline, and what is its throughput ceiling per the benchmark report? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 814.26 |
| q030 | multi_hop | What does the current employee handbook say about parental leave, and what additional weeks does the benefits FAQ mention? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 316.39 |
| q031 | multi_hop | Which data sources can Atlas connect to, and what does the Atlas Enterprise edition cost? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 442.74 |
| q032 | multi_hop | What is the SEV2 response time in the runbook, and what is the SLA credit percentage for Beacon? | 5 | 4 | 0.8 | 0.4444 | 0.4444 | — | n/a | n/a | — | 801.39 |
| q033 | multi_hop | How much does the Nimbus Enterprise tier cost, and what uptime guarantee does it receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 829.42 |
| q034 | multi_hop | What is the maximum catalog size tested for Marina, and which codename is the query engine? | 5 | 5 | 1.0 | 0.2941 | 0.5882 | — | n/a | n/a | — | 780.39 |
| q035 | multi_hop | What encryption does the privacy policy promise at rest, and what does the security policy require for restricted data? | 5 | 1 | 0.2 | 0.3333 | 0.3333 | — | n/a | n/a | — | 359.78 |
| q036 | multi_hop | Which product integrates with Slack, and how much does its Standard tier cost? | 5 | 4 | 0.8 | 0.0976 | 0.2439 | — | n/a | n/a | — | 802.79 |
| q037 | multi_hop | What is the equity vesting schedule in the employee handbook, and what is the 401(k) match percentage? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 838.82 |
| q038 | multi_hop | How long does the runbook say an incident can run before escalating to the VP of Engineering, and what is the SLA's Nimbus lag commitment? | 5 | 3 | 0.6 | 0.75 | 0.75 | — | n/a | n/a | — | 795.0 |
| q039 | multi_hop | Which two data sources can Atlas and Nimbus both write to according to the feature comparison? | 5 | 3 | 0.6 | 0.5 | 0.6667 | — | n/a | n/a | — | 831.74 |
| q040 | multi_hop | What is the backpressure onset lag measured for Kestrel, and which Kafka-based product does it power? | 5 | 3 | 0.6 | 0.0769 | 0.2564 | — | n/a | n/a | — | 805.81 |
| q041 | ambiguous | What is the current data retention period in the Aurora Labs privacy policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 330.91 |
| q042 | ambiguous | How many PTO days do employees get per year? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 247.63 |
| q043 | ambiguous | What is the renewal term in the Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 797.69 |
| q044 | ambiguous | What does Atlas cost? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 485.23 |
| q045 | ambiguous | What is the uptime guarantee for the Nimbus pipeline? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 814.77 |
| q046 | ambiguous | What encryption does Aurora Labs use for data at rest? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 322.05 |
| q047 | ambiguous | What happens to customer content after the subscription term ends? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 297.99 |
| q048 | ambiguous | What is the p95 query latency target for Atlas? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 780.95 |
| q049 | ambiguous | Which document describes how to respond to a SEV1 incident? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 853.16 |
| q050 | ambiguous | What happens when an incident lasts more than 4 hours? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 876.11 |
| q051 | ambiguous | What is the Nimbus pipeline lag commitment? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 865.58 |
| q052 | ambiguous | How many PTO days carry over into the next year? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 867.87 |
| q053 | unanswerable | What is Aurora Labs' revenue for fiscal year 2024? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 452.53 |
| q054 | unanswerable | What is the email address of Aurora Labs' CEO? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 428.25 |
| q055 | unanswerable | What is the interest rate on Aurora Labs' line of credit? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 376.85 |
| q056 | unanswerable | How many employees does Aurora Labs have in Tokyo? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 304.71 |
| q057 | unanswerable | What is the version number of the Aurora mobile app? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 310.77 |
| q058 | single_hop | What is the maximum number of concurrent queries Calcite sustained in the benchmark? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 719.48 |
| q059 | single_hop | What is the Nimbus Free tier price? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 784.49 |
| q060 | single_hop | How long does Aurora Labs respond to a verified data subject access request? | 5 | 4 | 0.8 | 0.3077 | 0.3077 | — | n/a | n/a | — | 335.14 |
| q061 | single_hop | What is the p95 write latency of Marina? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 834.95 |
| q062 | single_hop | What is the monthly uptime guarantee for Atlas analytics? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 465.06 |
| q063 | single_hop | How long are Aurora Labs usage telemetry records retained under the current policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 314.09 |
| q064 | single_hop | What is the health insurance premium coverage for employee dependents? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 242.03 |
| q065 | single_hop | Which error code does the API return for rate limit exceeded? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 390.4 |
| q066 | single_hop | What is the standard Nimbus monthly price for the Standard tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 922.65 |
| q067 | single_hop | How many weeks of paid parental leave do new parents receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 287.58 |
| q068 | single_hop | What is the liability cap in the current Acme MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 780.35 |
| q069 | single_hop | How many production regions does the Aurora Labs platform run in? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 311.77 |
| q070 | multi_hop | What is the Beacon delivery delay limit in the runbook, and what uptime guarantee does Beacon carry in the SLA? | 5 | 2 | 0.4 | 0.6667 | 0.6667 | — | n/a | n/a | — | 778.07 |
| q071 | multi_hop | What does the runbook say to check when Atlas query timeouts occur, and what is the SLA latency target for Atlas? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 827.25 |
| q072 | multi_hop | Which regions host customer data per the GDPR FAQ, and what is the retention period for usage telemetry in the current privacy policy? | 5 | 1 | 0.2 | 0.0667 | 0.2 | — | n/a | n/a | — | 588.99 |
