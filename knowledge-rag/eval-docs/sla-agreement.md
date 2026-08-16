# Aurora Labs Service Level Agreement

*Applicable to Atlas, Beacon, and Nimbus. Effective 2025-02-01.*

## 1. Service commitments

| Service | Monthly uptime guarantee | Credits |
| --- | --- | --- |
| Atlas analytics | 99.9% | 10% of monthly fee per 0.1% below |
| Beacon alerting | 99.95% | 10% of monthly fee per 0.05% below |
| Nimbus pipeline | 99.9% | 10% of monthly fee per 0.1% below |

The Nimbus pipeline guarantee covers the ingestion and transformation stages
end to end. Scheduled maintenance windows (announced at least 7 days in
advance) are excluded from uptime calculations, as are failures caused by
customer misconfiguration, unsupported third-party integrations, or force
majeure events.

## 2. Performance commitments

Atlas p95 query latency must remain below 2 seconds during normal operation.
Beacon must deliver alerts to webhook endpoints within 10 minutes of the
triggering event under normal conditions. Nimbus pipeline lag must remain
below 30 minutes for standard workloads.

## 3. Credits and claims

Service credits are issued as account credits and do not convert to cash.
To claim a credit, the customer must file a claim within 30 days of the end
of the month in which the downtime occurred, including the incident
identifiers from the status page. Aurora Labs will validate the claim within
10 business days.

## 4. Exclusions

This SLA does not cover beta features, customer-caused incidents, or
maintenance performed with prior notice. Downtime caused by failures of
customer-managed infrastructure is excluded.

## 5. Definitions

"Monthly uptime" is calculated as (total minutes in month - downtime
minutes) / total minutes in month, expressed as a percentage. "Downtime"
means the service is not available for more than 5 consecutive minutes.

## 6. Nimbus Enterprise tier

Customers on the Nimbus Enterprise tier receive an enhanced guarantee of
99.99% monthly uptime for the pipeline, and a 30-minute maximum pipeline
lag commitment. Claims follow the same process in section 3.
