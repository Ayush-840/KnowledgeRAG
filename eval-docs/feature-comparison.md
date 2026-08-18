# Aurora Labs Product Comparison

Compare Atlas, Beacon, and Nimbus to find the right fit for your team.

## Atlas — analytics platform

Atlas is Aurora Labs' business intelligence and analytics platform. It
connects to your data warehouse, builds dashboards, and supports SQL queries
over large datasets.

Key features:
- Drag-and-drop dashboard builder with 40+ chart types
- Native SQL query editor with autocomplete
- Scheduled email and Slack report delivery
- Row-level security and SSO (SAML, OIDC)
- Integrations: Snowflake, BigQuery, Postgres, Redshift

Atlas is built for teams that live in their warehouse. Dashboards are
versioned, and every change is recorded in the audit log. Scheduled reports
can be delivered daily, weekly, or monthly to email or Slack, and dashboards
can be embedded in your own application with an iframe or the Atlas embed
SDK. Atlas supports scheduled refreshes of materialized views and caches
query results so frequent dashboards do not hammer your warehouse. The
query editor includes a live explain plan, query cost estimation, and a
favorites system shared across the workspace.

## Beacon — alerting and monitoring

Beacon is Aurora Labs' alerting service. It watches metrics and log streams,
applies threshold and anomaly-detection rules, and routes alerts to Slack,
email, PagerDuty, or webhooks.

Key features:
- Threshold, heartbeat, and ML-based anomaly detection
- Alert deduplication and escalation chains
- Runbook links attached to every alert
- Integrates with Datadog, Prometheus, and CloudWatch

Beacon is designed to reduce alert noise. Every alert rule has a
deduplication window, and alerts can be grouped by service, environment, or
customer. Escalation chains route alerts to the correct team in order, and
each alert can carry a runbook link so the responder lands on the right
procedure. Beacon supports maintenance windows, mute rules, and alert
schedules, so on-call rotations are not woken for known maintenance. The ML
anomaly detector learns the baseline of each metric and flags deviations
without requiring static thresholds.

## Nimbus — data pipeline

Nimbus is Aurora Labs' streaming data pipeline. It ingests events, applies
transformations, and loads results into your warehouse or data lake.

Key features:
- Exactly-once event delivery with Kafka
- Visual transform builder plus Python SDK
- Automatic schema drift handling
- Backfill and replay from any point in time
- Sinks: S3, Snowflake, BigQuery, Redshift, Postgres

Nimbus consumes events from Kafka, applies streaming transforms (filters,
joins, aggregations, enrichment), and writes to your sink of choice. The
visual transform builder covers the common cases without code, while the
Python SDK gives data engineers full control. Pipeline state is checkpointed
continuously, which is what makes replay from any point in time possible.
Schema drift is detected automatically: new fields are added to the target
schema by default, and breaking changes are quarantined for review rather
than failing the pipeline.

## Feature matrix

| Capability | Atlas | Beacon | Nimbus |
| --- | --- | --- | --- |
| Dashboards | yes | no | no |
| SQL query editor | yes | no | no |
| Scheduled reports | yes | no | no |
| Threshold alerts | no | yes | no |
| Anomaly detection | no | yes | no |
| Escalation chains | no | yes | no |
| Streaming ingestion | no | no | yes |
| Transform builder | no | no | yes |
| Replay / backfill | no | no | yes |
| SSO (SAML/OIDC) | yes | yes | yes |
| Audit log | yes | yes | yes |
| REST API | yes | yes | yes |

## Pricing tiers at a glance

Pricing details live in product-pricing.csv. In summary: Atlas and Beacon are
per-user products with Starter, Standard, and Enterprise tiers; Nimbus is
per-pipeline with Free, Starter, Standard, Enterprise, and Enterprise Plus
tiers. All per-user tiers require an annual commitment at the listed price;
monthly billing is available at a 20% surcharge. See the pricing sheet for
exact numbers.

## Which one should you pick?

- Analysts who need dashboards and SQL: Atlas
- Platform teams who need alerting: Beacon
- Data engineers who need pipelines: Nimbus

Most customers start with one product; all three share a single sign-on,
billing, and administration console. See product-pricing.csv for pricing
details, and the atlas-product-sheet for Atlas specifics.

## Combining products

The products are designed to work together. A typical Aurora Labs
deployment looks like this: Nimbus ingests raw events and loads them into
the warehouse, Atlas builds dashboards on top of that data, and Beacon
watches both the pipeline and the warehouse for anomalies, alerting the
on-call team through its escalation chains. Teams that combine products
share one admin console, one audit log, and one support ticket, which is
why the combined bundle is billed as a single invoice. See the platform
architecture report (platform-report-part1.md and platform-report-part2.md)
for the reference architecture.

## Atlas deeper dive

Atlas connects to your warehouse through a managed connection that holds
credentials encrypted at rest and refreshes them on rotation. The query
editor supports tabs, saved snippets, and a shared query library. Results
can be exported to CSV, JSON, or Excel, and dashboards can be filtered
interactively without re-running the underlying query. Atlas caches
materialized views on a schedule, and the cache can be pinned so
cost-sensitive dashboards never hit the warehouse during business hours.
Row-level security is defined per team and applies to every query, and
queries run by a user only ever see the rows their policy allows.

## Beacon deeper dive

Beacon evaluates alert rules on a configurable interval, from 30 seconds
to 24 hours. Each rule has a severity, a deduplication window, and a list
of channels; channels can be assigned per escalation step, so a SEV1
condition can page while a SEV3 condition only posts to Slack. The ML
anomaly detector learns baselines over a configurable lookback window and
flags deviations above a sensitivity setting. Alert history is retained
for 90 days on Standard and 2 years on Enterprise. Beacon integrates with
Datadog, Prometheus, and CloudWatch by ingesting their metric streams, so
teams do not need to duplicate alert rules.

## Nimbus deeper dive

The visual transform builder covers filters, lookups, aggregations,
windows, and joins without code. For custom logic, the Python SDK runs in
an isolated sandbox with configurable dependencies. Nimbus writes to S3,
Snowflake, BigQuery, Redshift, and Postgres sinks, with schema drift
handled per the platform architecture report. Replays re-ingest events
from any retained point in time and run in parallel with the live
pipeline. Nimbus billing is per pipeline per month; the pricing sheet
lists the tiers and the per-pipeline limits that apply to each (Starter
includes 1 pipeline and 50 GB/hour ingestion; Enterprise Plus includes
unlimited pipelines and 500 GB/hour).
