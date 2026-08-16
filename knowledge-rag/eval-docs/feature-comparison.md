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

## Beacon — alerting and monitoring

Beacon is Aurora Labs' alerting service. It watches metrics and log streams,
applies threshold and anomaly-detection rules, and routes alerts to Slack,
email, PagerDuty, or webhooks.

Key features:
- Threshold, heartbeat, and ML-based anomaly detection
- Alert deduplication and escalation chains
- Runbook links attached to every alert
- Integrates with Datadog, Prometheus, and CloudWatch

## Nimbus — data pipeline

Nimbus is Aurora Labs' streaming data pipeline. It ingests events, applies
transformations, and loads results into your warehouse or data lake.

Key features:
- Exactly-once event delivery with Kafka
- Visual transform builder plus Python SDK
- Automatic schema drift handling
- Backfill and replay from any point in time
- Sinks: S3, Snowflake, BigQuery, Redshift, Postgres

## Which one should you pick?

- Analysts who need dashboards and SQL: Atlas
- Platform teams who need alerting: Beacon
- Data engineers who need pipelines: Nimbus

Most customers start with one product; all three share a single sign-on,
billing, and administration console. See product-pricing.csv for pricing
details, and the atlas-product-sheet for Atlas specifics.
