# Knowledge RAG — Evaluation Report

- Generated: 2026-08-21T22:19:12.169705+00:00
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
| mean_total_latency_ms | 696.7721 |

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
| q001 | single_hop | How much does Atlas Standard cost per user per month? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 7186.31 |
| q002 | single_hop | What monthly uptime guarantee does Beacon offer under the SLA? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 368.26 |
| q003 | single_hop | What is the p95 warm query latency of the Calcite query engine? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 793.09 |
| q004 | single_hop | What percentage does Aurora Labs match on employee 401(k) contributions? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 365.71 |
| q005 | single_hop | How quickly must an on-call engineer acknowledge a SEV1 page? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 787.12 |
| q006 | single_hop | What is the SKU of the Atlas analytics platform? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 792.72 |
| q007 | single_hop | What is the annual fee Acme Corp pays under the current Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 804.41 |
| q008 | single_hop | Which Aurora Labs product is the alerting and monitoring service? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 804.52 |
| q009 | single_hop | What is the base URL of the Aurora Labs REST API? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 329.49 |
| q010 | single_hop | How long is the probation period for new hires at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 283.31 |
| q011 | single_hop | How many named users does Acme Corp get under the current MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 787.87 |
| q012 | single_hop | What is the codename of the stream processor behind Nimbus? | 5 | 2 | 0.4 | 0.1818 | 0.1818 | — | n/a | n/a | — | 795.39 |
| q013 | single_hop | How many chart types does the Atlas dashboard builder support? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 791.47 |
| q014 | single_hop | What is the Nimbus Enterprise monthly uptime guarantee? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 818.77 |
| q015 | single_hop | What is the API rate limit for the free tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 798.03 |
| q016 | single_hop | How long after an incident must the post-incident review be completed? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 813.98 |
| q017 | single_hop | What is the wellness stipend amount per month? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 798.66 |
| q018 | single_hop | Which codename is used for the Aurora Labs catalog service? | 5 | 1 | 0.2 | 0.0625 | 0.3125 | — | n/a | n/a | — | 510.07 |
| q019 | single_hop | How often must API keys be rotated according to the security policy? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 403.63 |
| q020 | single_hop | What is the p95 write latency of the Marina catalog service? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 806.55 |
| q021 | single_hop | What is the learning budget per employee per year? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 834.82 |
| q022 | single_hop | Who is Aurora Labs' EU representative under GDPR? | 5 | 4 | 0.8 | 1.0 | 1.0 | — | n/a | n/a | — | 299.89 |
| q023 | single_hop | What is the p95 end-to-end processing latency of Kestrel? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 781.85 |
| q024 | single_hop | What is the initial term of the current Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 788.45 |
| q025 | multi_hop | Which product does the Calcite query engine power, and what is its warm p95 latency? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 699.76 |
| q026 | multi_hop | What happens when Nimbus pipeline lag exceeds 30 minutes, and what does the SLA commit for pipeline lag? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 791.83 |
| q027 | multi_hop | What uptime guarantee does the product behind Beacon offer, and what pricing tier is available? | 5 | 2 | 0.4 | 0.6667 | 0.6667 | — | n/a | n/a | — | 452.45 |
| q028 | multi_hop | What is the retention period in the version of the privacy policy that supersedes Version 1? | 5 | 2 | 0.4 | 0.6667 | 1.0 | — | n/a | n/a | — | 304.96 |
| q029 | multi_hop | Which service does the incident runbook say powers the data pipeline, and what is its throughput ceiling per the benchmark report? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 902.12 |
| q030 | multi_hop | What does the current employee handbook say about parental leave, and what additional weeks does the benefits FAQ mention? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 275.25 |
| q031 | multi_hop | Which data sources can Atlas connect to, and what does the Atlas Enterprise edition cost? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 443.12 |
| q032 | multi_hop | What is the SEV2 response time in the runbook, and what is the SLA credit percentage for Beacon? | 5 | 4 | 0.8 | 0.4444 | 0.4444 | — | n/a | n/a | — | 805.18 |
| q033 | multi_hop | How much does the Nimbus Enterprise tier cost, and what uptime guarantee does it receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 813.9 |
| q034 | multi_hop | What is the maximum catalog size tested for Marina, and which codename is the query engine? | 5 | 5 | 1.0 | 0.2941 | 0.5882 | — | n/a | n/a | — | 783.72 |
| q035 | multi_hop | What encryption does the privacy policy promise at rest, and what does the security policy require for restricted data? | 5 | 1 | 0.2 | 0.3333 | 0.3333 | — | n/a | n/a | — | 372.79 |
| q036 | multi_hop | Which product integrates with Slack, and how much does its Standard tier cost? | 5 | 4 | 0.8 | 0.0976 | 0.2439 | — | n/a | n/a | — | 790.28 |
| q037 | multi_hop | What is the equity vesting schedule in the employee handbook, and what is the 401(k) match percentage? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 789.46 |
| q038 | multi_hop | How long does the runbook say an incident can run before escalating to the VP of Engineering, and what is the SLA's Nimbus lag commitment? | 5 | 3 | 0.6 | 0.75 | 0.75 | — | n/a | n/a | — | 796.88 |
| q039 | multi_hop | Which two data sources can Atlas and Nimbus both write to according to the feature comparison? | 5 | 3 | 0.6 | 0.5 | 0.6667 | — | n/a | n/a | — | 774.37 |
| q040 | multi_hop | What is the backpressure onset lag measured for Kestrel, and which Kafka-based product does it power? | 5 | 3 | 0.6 | 0.0769 | 0.2564 | — | n/a | n/a | — | 839.8 |
| q041 | ambiguous | What is the current data retention period in the Aurora Labs privacy policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 321.29 |
| q042 | ambiguous | How many PTO days do employees get per year? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 245.65 |
| q043 | ambiguous | What is the renewal term in the Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 805.26 |
| q044 | ambiguous | What does Atlas cost? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 454.18 |
| q045 | ambiguous | What is the uptime guarantee for the Nimbus pipeline? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 783.3 |
| q046 | ambiguous | What encryption does Aurora Labs use for data at rest? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 285.5 |
| q047 | ambiguous | What happens to customer content after the subscription term ends? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 280.93 |
| q048 | ambiguous | What is the p95 query latency target for Atlas? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 779.33 |
| q049 | ambiguous | Which document describes how to respond to a SEV1 incident? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 781.4 |
| q050 | ambiguous | What happens when an incident lasts more than 4 hours? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 780.96 |
| q051 | ambiguous | What is the Nimbus pipeline lag commitment? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 781.21 |
| q052 | ambiguous | How many PTO days carry over into the next year? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 783.71 |
| q053 | unanswerable | What is Aurora Labs' revenue for fiscal year 2024? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 384.98 |
| q054 | unanswerable | What is the email address of Aurora Labs' CEO? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 423.41 |
| q055 | unanswerable | What is the interest rate on Aurora Labs' line of credit? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 327.51 |
| q056 | unanswerable | How many employees does Aurora Labs have in Tokyo? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 298.51 |
| q057 | unanswerable | What is the version number of the Aurora mobile app? | 5 | 0 | 0.0 | 0.0 | 0.0 | — | n/a | n/a | — | 279.31 |
| q058 | single_hop | What is the maximum number of concurrent queries Calcite sustained in the benchmark? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 683.86 |
| q059 | single_hop | What is the Nimbus Free tier price? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 792.58 |
| q060 | single_hop | How long does Aurora Labs respond to a verified data subject access request? | 5 | 4 | 0.8 | 0.3077 | 0.3077 | — | n/a | n/a | — | 290.33 |
| q061 | single_hop | What is the p95 write latency of Marina? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 794.4 |
| q062 | single_hop | What is the monthly uptime guarantee for Atlas analytics? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 420.89 |
| q063 | single_hop | How long are Aurora Labs usage telemetry records retained under the current policy? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 320.71 |
| q064 | single_hop | What is the health insurance premium coverage for employee dependents? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 225.37 |
| q065 | single_hop | Which error code does the API return for rate limit exceeded? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 379.51 |
| q066 | single_hop | What is the standard Nimbus monthly price for the Standard tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 789.09 |
| q067 | single_hop | How many weeks of paid parental leave do new parents receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | — | n/a | n/a | — | 239.22 |
| q068 | single_hop | What is the liability cap in the current Acme MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | — | n/a | n/a | — | 790.26 |
| q069 | single_hop | How many production regions does the Aurora Labs platform run in? | 5 | 1 | 0.2 | 0.5 | 0.5 | — | n/a | n/a | — | 283.37 |
| q070 | multi_hop | What is the Beacon delivery delay limit in the runbook, and what uptime guarantee does Beacon carry in the SLA? | 5 | 2 | 0.4 | 0.6667 | 0.6667 | — | n/a | n/a | — | 788.91 |
| q071 | multi_hop | What does the runbook say to check when Atlas query timeouts occur, and what is the SLA latency target for Atlas? | 5 | 3 | 0.6 | 1.0 | 1.0 | — | n/a | n/a | — | 826.52 |
| q072 | multi_hop | Which regions host customer data per the GDPR FAQ, and what is the retention period for usage telemetry in the current privacy policy? | 5 | 1 | 0.2 | 0.0667 | 0.2 | — | n/a | n/a | — | 565.89 |
