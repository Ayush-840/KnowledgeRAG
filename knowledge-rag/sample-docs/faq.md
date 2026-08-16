# Aurora Labs FAQ

## Getting started

You can start a free 14-day trial of Atlas without a credit card. Trial
accounts include full access to real-time dashboards and custom reporting.
To sign up, you need a work email address and an organization name; trials
convert automatically to a paid plan unless you cancel before day 14.

## Billing

All plans are billed monthly and can be cancelled at any time. Atlas costs
$49 per user per month, and Beacon costs $19 per user per month. Annual
billing receives a 20 percent discount, and invoices are issued on the first
day of each billing period. You can change your payment method at any time
from the billing settings page.

## Pricing

Atlas Pro costs $99 per user per month and adds single sign-on and audit
logs. Beacon Plus costs $39 per user per month and adds on-call scheduling.
Nimbus uses custom pricing based on data volume, and Nimbus Lite is $29 per
month for up to 100,000 events. Volume discounts start at 50 seats, and
annual contracts are quoted on request.

## Refunds

Unused subscription time is refunded on a prorated basis when you cancel
mid-cycle. If you cancel within the first 14 days of a paid plan, you receive
a full refund of the first invoice. Refunds are issued to the original
payment method within 5 business days, and enterprise contracts follow the
terms of their negotiated agreement.

## Security

Customer data is encrypted at rest with AES-256 and in transit with TLS 1.3.
Aurora Labs holds a SOC 2 Type II certification and is GDPR compliant. Data
centers are monitored 24/7, and access to production systems requires
multi-factor authentication. Security assessments are available to
enterprise customers under a mutual NDA.

## Data retention

Standard plans retain 30 days of event history; Atlas Pro retains 90 days.
Enterprise contracts can negotiate custom retention windows of up to 7
years. Deleted workspaces are purged from backups within 30 days, and you
can request a full data export at any time from the workspace settings.

## Integrations

Beacon integrates with Slack and Microsoft Teams out of the box. Nimbus
connects to more than 60 data sources, and Atlas connects to web analytics
and advertising platforms. The public REST API supports webhooks, and
pre-built connectors are available for Salesforce, HubSpot, and Snowflake.

## API

The REST API is rate-limited to 100 requests per minute on standard plans
and 1,000 requests per minute on Pro plans. API keys are scoped per workspace
and can be rotated from the developer settings page. Every response includes
an X-RateLimit-Remaining header, and the API returns 429 with a Retry-After
header when the limit is exceeded.

## Uptime and SLA

Atlas and Beacon target 99.9 percent uptime. Nimbus Enterprise and Atlas
Enterprise offer a 99.99 percent uptime service-level agreement with service
credits for breaches. Status is published at status.auroralabs.com, and
incident post-mortems are shared publicly within 7 days of resolution.

## Enterprise

Enterprise plans include dedicated support engineers, custom data retention,
SSO through SAML and OAuth, and the option to deploy in your own cloud
account. A solutions architect joins your onboarding call, and quarterly
business reviews are included. Enterprise customers can negotiate annual
contracts with volume pricing.

## Onboarding

Guided onboarding includes a kickoff call, data source setup, and a custom
dashboard workshop. Most teams go live within two weeks. Migration tooling
imports dashboards and alerts from legacy analytics platforms, and the
migration guide covers schema mapping and downtime planning.

## Support hours

Standard plans receive email support with a four-hour response target during
business hours. Pro plans get a two-hour target and priority queue placement.
Enterprise customers receive 24/7 support with a one-hour response time and
a dedicated support engineer in their Slack workspace.

## Trials and conversion

Trials do not require a credit card. When a trial ends, the workspace is
paused rather than deleted, and you can resume at any time within 90 days.
Trial data is preserved for conversion, and sales can extend trials to 30
days for evaluation teams on request.
