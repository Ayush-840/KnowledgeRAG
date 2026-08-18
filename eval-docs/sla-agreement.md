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

These performance commitments are measured over each calendar month. Beacon's
delivery commitment is measured from the moment the alert rule condition is
satisfied to the moment the webhook endpoint acknowledges receipt. Atlas
latency is measured from the customer's dashboard or API, excluding the first
cold query after a workspace upgrade, and is reported in the customer
workspace's monitoring view.

## 3. Credits and claims

Service credits are issued as account credits and do not convert to cash.
To claim a credit, the customer must file a claim within 30 days of the end
of the month in which the downtime occurred, including the incident
identifiers from the status page. Aurora Labs will validate the claim within
10 business days.

Credits are calculated per service. A customer who experienced Atlas downtime
of 0.3% in a month receives 30% of the Atlas monthly fee as a credit
(10% per 0.1% below the 99.9% guarantee). Credits for Beacon are calculated
per 0.05% below the 99.95% guarantee. Approved credits are applied to the
next invoice, and no single claim may exceed 100% of the monthly fee for the
affected service. Repeated incidents in the same calendar month are combined
for the purposes of the calculation.

## 4. Exclusions

This SLA does not cover beta features, customer-caused incidents, or
maintenance performed with prior notice. Downtime caused by failures of
customer-managed infrastructure is excluded.

Additional exclusions: downtime during the first 30 days after a workspace
migration to a new region, failures of customer networks between the
customer's environment and Aurora Labs' endpoints, and degradation caused by
customer workloads that exceed the documented rate limits of the service
(Atlas: 1,000 queries per hour per workspace; Beacon: 500 webhooks per
minute; Nimbus: 50 GB per hour ingestion). Where an exclusion applies,
Aurora Labs will document the reason on the claim.

## 5. Definitions

"Monthly uptime" is calculated as (total minutes in month - downtime
minutes) / total minutes in month, expressed as a percentage. "Downtime"
means the service is not available for more than 5 consecutive minutes.

"Not available" means the service returns errors for more than 5% of
requests during the measured window, or the service is unreachable from the
customer's region. A single failed request does not constitute downtime;
downtime is measured in consecutive minutes of degraded availability. The
status page incident log is the authoritative record for downtime
calculations, and customers may dispute a calculation by referencing
incident identifiers within the claim window.

## 6. Nimbus Enterprise tier

Customers on the Nimbus Enterprise tier receive an enhanced guarantee of
99.99% monthly uptime for the pipeline, and a 30-minute maximum pipeline
lag commitment. Claims follow the same process in section 3.

## 7. Maintenance windows

Scheduled maintenance is announced at least 7 days in advance through the
status page and by email to workspace administrators. Maintenance is
scheduled outside business hours in the customer's primary region whenever
possible, between 02:00 and 06:00 local time. Emergency maintenance required
to protect the security or integrity of the platform may be performed with
as much notice as the situation allows, and does not count toward the uptime
guarantee when the emergency is caused by a security threat to the platform
as a whole.

## 8. Support and response times

The SLA works together with the support plan on the customer's contract:

| Severity | Initial response target | Example |
| --- | --- | --- |
| SEV1 | 30 minutes, 24/7 | Service outage or data loss |
| SEV2 | 4 business hours | Significant degradation |
| SEV3 | 1 business day | Minor issue with workaround |
| SEV4 | 2 business days | Cosmetic or feature request |

Response targets begin when the ticket is filed through the support portal
with the correct severity. Customers who do not have a support plan on
their contract receive best-effort support and are not covered by these
response targets.

## 9. Availability reporting

Each month, Aurora Labs publishes the measured uptime for each service on
the status page's monthly report. The report includes the number of downtime
incidents, their total duration, and the resulting guaranteed uptime for the
month. Customers may use the report as the basis for claims, though claims
still require incident identifiers.

## 10. Changes to this SLA

Aurora Labs may update this SLA from time to time. Material changes are
announced at least 30 days before they take effect, and existing customers
may terminate their contract without penalty within 14 days of a material
change that reduces their guarantees. The version in effect on the first day
of the month in which downtime occurred governs any claim.

## 11. Worked example of a credit calculation

Consider a customer on the Atlas Standard tier ($49 per user, 50 users,
$2,450 monthly fee) who experiences Atlas downtime of 45 minutes in a
month. Monthly uptime is (43,200 - 45) / 43,200 = 99.896%, which is below
the 99.9% guarantee by 0.004 percentage points. Because the guarantee
uses a per-0.1% step, a shortfall of 0.004% rounds up to a single 0.1%
step, yielding a credit of 10% of the monthly fee: $245. If the same
month had two separate incidents totaling 1 hour of downtime (99.861%
uptime, a 0.039% shortfall), the credit is still 10% of the fee, because
the shortfall does not reach the next 0.1% step. Credits never exceed
100% of the monthly fee, which would require a shortfall of more than
1.0 percentage point.

## 12. Nimbus pipeline lag credits

The Nimbus performance commitment (lag below 30 minutes) is enforced
separately from the uptime guarantee. If the measured pipeline lag exceeds
30 minutes for more than 120 minutes in a calendar month on the Standard
tier or above, the customer receives a 15% credit on the Nimbus fee for
that month. The lag is measured from the pipeline's `lag_minutes` metric
in the console. Enterprise tier customers receive the same credit at a
10% rate because their enhanced guarantee is already priced in.

## 13. Multi-region deployments

The SLA applies per region for customers with deployments in multiple
regions. A customer with workspaces in us-east-1 and eu-central-1
evaluates uptime separately for each region, and credits are calculated
per region against the fee attributable to that region. Downtime in one
region does not offset availability in another. Customers can request
region-level uptime reports from the monthly availability report.
