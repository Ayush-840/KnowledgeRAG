# Knowledge RAG — Evaluation Report

- Generated: 2026-08-16T17:50:53.646876+00:00
- Documents: api-reference.md, atlas-product-sheet.pdf, benefits-faq.md, employee-handbook-v1.md, employee-handbook-v2.md, feature-comparison.md, gdpr-faq.md, incident-runbook.txt, oncall-handbook.md, platform-report-part1.md, platform-report-part2.md, privacy-policy-v1.md, privacy-policy-v2.md, product-pricing.csv, security-policy.docx, sla-agreement.md, vendor-contract-v2.md, vendor-contract.md
- Settings: chunk_size=500, overlap=100, strategy=fixed, candidates=20, top_k=5, reranker=True
- LLM judge: meta/llama-3.3-70b-instruct (enabled=True)

## Summary

| Metric | Mean |
| --- | --- |
| context_precision | 0.2861 |
| context_recall | 0.6936 |
| recall_at_pool | 0.8533 |
| faithfulness | n/a |
| answer_relevance | n/a |
| mean_generation_ms | n/a |
| mean_total_latency_ms | 910.0518 |

### By query type

| Type | n | Precision | Recall | Recall@pool | Faithfulness | Ans. rel. |
| --- | --- | --- | --- | --- | --- | --- |
| ambiguous | 12 | 0.1833 | 0.75 | 0.9167 | n/a | n/a |
| multi_hop | 19 | 0.4737 | 0.5547 | 0.867 | n/a | n/a |
| single_hop | 36 | 0.2611 | 0.8445 | 0.9435 | n/a | n/a |
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
| q001 | single_hop | How much does Atlas Standard cost per user per month? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 6957.23 |
| q002 | single_hop | What monthly uptime guarantee does Beacon offer under the SLA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 837.74 |
| q003 | single_hop | What is the p95 warm query latency of the Calcite query engine? | 5 | 2 | 0.4 | 0.6667 | 1.0 | n/a | n/a | 823.65 |
| q004 | single_hop | What percentage does Aurora Labs match on employee 401(k) contributions? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 809.41 |
| q005 | single_hop | How quickly must an on-call engineer acknowledge a SEV1 page? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 817.36 |
| q006 | single_hop | What is the SKU of the Atlas analytics platform? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 820.15 |
| q007 | single_hop | What is the annual fee Acme Corp pays under the current Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 795.17 |
| q008 | single_hop | Which Aurora Labs product is the alerting and monitoring service? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 804.91 |
| q009 | single_hop | What is the base URL of the Aurora Labs REST API? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 797.91 |
| q010 | single_hop | How long is the probation period for new hires at Aurora Labs? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 799.53 |
| q011 | single_hop | How many named users does Acme Corp get under the current MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 794.93 |
| q012 | single_hop | What is the codename of the stream processor behind Nimbus? | 5 | 1 | 0.2 | 0.1429 | 0.5714 | n/a | n/a | 794.82 |
| q013 | single_hop | How many chart types does the Atlas dashboard builder support? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 804.51 |
| q014 | single_hop | What is the Nimbus Enterprise monthly uptime guarantee? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 807.78 |
| q015 | single_hop | What is the API rate limit for the free tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 799.74 |
| q016 | single_hop | How long after an incident must the post-incident review be completed? | 5 | 1 | 0.2 | 0.5 | 0.5 | n/a | n/a | 804.32 |
| q017 | single_hop | What is the wellness stipend amount per month? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 799.69 |
| q018 | single_hop | Which codename is used for the Aurora Labs catalog service? | 5 | 1 | 0.2 | 0.1111 | 0.7778 | n/a | n/a | 795.05 |
| q019 | single_hop | How often must API keys be rotated according to the security policy? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 791.6 |
| q020 | single_hop | What is the p95 write latency of the Marina catalog service? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 796.2 |
| q021 | single_hop | What is the learning budget per employee per year? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 793.8 |
| q022 | single_hop | Who is Aurora Labs' EU representative under GDPR? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 784.31 |
| q023 | single_hop | What is the p95 end-to-end processing latency of Kestrel? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 796.19 |
| q024 | single_hop | What is the initial term of the current Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 789.35 |
| q025 | multi_hop | Which product does the Calcite query engine power, and what is its warm p95 latency? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 817.84 |
| q026 | multi_hop | What happens when Nimbus pipeline lag exceeds 30 minutes, and what does the SLA commit for pipeline lag? | 5 | 2 | 0.4 | 0.6667 | 1.0 | n/a | n/a | 816.09 |
| q027 | multi_hop | What uptime guarantee does the product behind Beacon offer, and what pricing tier is available? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 800.38 |
| q028 | multi_hop | What is the retention period in the version of the privacy policy that supersedes Version 1? | 5 | 2 | 0.4 | 0.6667 | 1.0 | n/a | n/a | 811.49 |
| q029 | multi_hop | Which service does the incident runbook say powers the data pipeline, and what is its throughput ceiling per the benchmark report? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 809.62 |
| q030 | multi_hop | What does the current employee handbook say about parental leave, and what additional weeks does the benefits FAQ mention? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 866.02 |
| q031 | multi_hop | Which data sources can Atlas connect to, and what does the Atlas Enterprise edition cost? | 5 | 1 | 0.2 | 0.5 | 0.5 | n/a | n/a | 803.38 |
| q032 | multi_hop | What is the SEV2 response time in the runbook, and what is the SLA credit percentage for Beacon? | 5 | 5 | 1.0 | 0.5556 | 1.0 | n/a | n/a | 826.38 |
| q033 | multi_hop | How much does the Nimbus Enterprise tier cost, and what uptime guarantee does it receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 845.41 |
| q034 | multi_hop | What is the maximum catalog size tested for Marina, and which codename is the query engine? | 5 | 5 | 1.0 | 0.5556 | 0.8889 | n/a | n/a | 812.66 |
| q035 | multi_hop | What encryption does the privacy policy promise at rest, and what does the security policy require for restricted data? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 828.47 |
| q036 | multi_hop | Which product integrates with Slack, and how much does its Standard tier cost? | 5 | 3 | 0.6 | 0.1154 | 0.3846 | n/a | n/a | 824.55 |
| q037 | multi_hop | What is the equity vesting schedule in the employee handbook, and what is the 401(k) match percentage? | 5 | 3 | 0.6 | 1.0 | 1.0 | n/a | n/a | 839.55 |
| q038 | multi_hop | How long does the runbook say an incident can run before escalating to the VP of Engineering, and what is the SLA's Nimbus lag commitment? | 5 | 3 | 0.6 | 0.75 | 1.0 | n/a | n/a | 839.59 |
| q039 | multi_hop | Which two data sources can Atlas and Nimbus both write to according to the feature comparison? | 5 | 1 | 0.2 | 0.2 | 0.8 | n/a | n/a | 832.4 |
| q040 | multi_hop | What is the backpressure onset lag measured for Kestrel, and which Kafka-based product does it power? | 5 | 4 | 0.8 | 0.1538 | 0.4615 | n/a | n/a | 821.18 |
| q041 | ambiguous | What is the current data retention period in the Aurora Labs privacy policy? | 5 | 0 | 0.0 | 0.0 | 1.0 | n/a | n/a | 823.26 |
| q042 | ambiguous | How many PTO days do employees get per year? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 824.54 |
| q043 | ambiguous | What is the renewal term in the Acme Master Services Agreement? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 834.81 |
| q044 | ambiguous | What does Atlas cost? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 859.89 |
| q045 | ambiguous | What is the uptime guarantee for the Nimbus pipeline? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 836.18 |
| q046 | ambiguous | What encryption does Aurora Labs use for data at rest? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 836.5 |
| q047 | ambiguous | What happens to customer content after the subscription term ends? | 5 | 2 | 0.4 | 0.5 | 1.0 | n/a | n/a | 839.79 |
| q048 | ambiguous | What is the p95 query latency target for Atlas? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 849.57 |
| q049 | ambiguous | Which document describes how to respond to a SEV1 incident? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 834.29 |
| q050 | ambiguous | What happens when an incident lasts more than 4 hours? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 841.69 |
| q051 | ambiguous | What is the Nimbus pipeline lag commitment? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 838.31 |
| q052 | ambiguous | How many PTO days carry over into the next year? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 839.9 |
| q053 | unanswerable | What is Aurora Labs' revenue for fiscal year 2024? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 847.02 |
| q054 | unanswerable | What is the email address of Aurora Labs' CEO? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 874.22 |
| q055 | unanswerable | What is the interest rate on Aurora Labs' line of credit? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 842.29 |
| q056 | unanswerable | How many employees does Aurora Labs have in Tokyo? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 839.34 |
| q057 | unanswerable | What is the version number of the Aurora mobile app? | 5 | 0 | 0.0 | 0.0 | 0.0 | n/a | n/a | 833.4 |
| q058 | single_hop | What is the maximum number of concurrent queries Calcite sustained in the benchmark? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 837.89 |
| q059 | single_hop | What is the Nimbus Free tier price? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 844.08 |
| q060 | single_hop | How long does Aurora Labs respond to a verified data subject access request? | 5 | 3 | 0.6 | 0.2308 | 0.6154 | n/a | n/a | 837.55 |
| q061 | single_hop | What is the p95 write latency of Marina? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 855.27 |
| q062 | single_hop | What is the monthly uptime guarantee for Atlas analytics? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 842.61 |
| q063 | single_hop | How long are Aurora Labs usage telemetry records retained under the current policy? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 844.23 |
| q064 | single_hop | What is the health insurance premium coverage for employee dependents? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 826.91 |
| q065 | single_hop | Which error code does the API return for rate limit exceeded? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 835.1 |
| q066 | single_hop | What is the standard Nimbus monthly price for the Standard tier? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 835.19 |
| q067 | single_hop | How many weeks of paid parental leave do new parents receive? | 5 | 2 | 0.4 | 1.0 | 1.0 | n/a | n/a | 838.87 |
| q068 | single_hop | What is the liability cap in the current Acme MSA? | 5 | 1 | 0.2 | 1.0 | 1.0 | n/a | n/a | 837.39 |
| q069 | single_hop | How many production regions does the Aurora Labs platform run in? | 5 | 0 | 0.0 | 0.0 | 0.5 | n/a | n/a | 842.32 |
| q070 | multi_hop | What is the Beacon delivery delay limit in the runbook, and what uptime guarantee does Beacon carry in the SLA? | 5 | 1 | 0.2 | 0.5 | 1.0 | n/a | n/a | 837.67 |
| q071 | multi_hop | What does the runbook say to check when Atlas query timeouts occur, and what is the SLA latency target for Atlas? | 5 | 2 | 0.4 | 0.5 | 1.0 | n/a | n/a | 843.94 |
| q072 | multi_hop | Which regions host customer data per the GDPR FAQ, and what is the retention period for usage telemetry in the current privacy policy? | 5 | 2 | 0.4 | 0.125 | 0.4375 | n/a | n/a | 859.35 |
