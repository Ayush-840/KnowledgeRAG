# Aurora Labs GDPR FAQ

Frequently asked questions about how Aurora Labs handles the EU General Data
Protection Regulation (GDPR) for customers using Atlas, Beacon, and Nimbus.

## What is Aurora Labs' role under GDPR?

For most customer content, Aurora Labs acts as a **data processor** on behalf
of the customer, who is the controller. For Aurora Labs' own account data
(name, work email, billing address), we act as controller.

## Does Aurora Labs offer a Data Processing Agreement (DPA)?

Yes. A DPA is incorporated into the standard terms of service and is also
available for separate signature. It covers Article 28 requirements including
instructions, confidentiality, and audit rights.

## Where is customer data stored?

Customer data is stored in the region selected at workspace creation:
us-east-1 (United States), eu-central-1 (European Union), or ap-southeast-2
(Asia Pacific). Data does not leave the selected region except for support
access under the DPA.

## How are data subject access requests (DSARs) handled?

Customers can raise DSARs through the support portal or by emailing
dpo@auroralabs.example. Aurora Labs will fulfill a verified request within
30 days, extendable by two further months where the request is complex.

## Does Aurora Labs rely on Standard Contractual Clauses?

Yes, for transfers of personal data from the EEA to the United States,
Aurora Labs relies on EU Standard Contractual Clauses (2021/914) together
with a transfer impact assessment.

## What about the right to erasure?

Data subjects can request erasure of their personal data. Aurora Labs will
delete the data unless a legal obligation to retain it applies, in which case
retention is limited to the required statutory period.

## How does Aurora Labs support data portability?

We provide workspace export in JSON format for customer content, available
through the admin console under Settings > Export.

## Who is Aurora Labs' EU representative?

Aurora Labs has appointed Aurora Labs Ireland Ltd, 12 Grand Canal Square,
Dublin 2, as its representative in the EU for GDPR purposes.

## Does Aurora Labs maintain records of processing activities?

Yes. Aurora Labs maintains a register of processing activities under Article
30 covering the categories of data we process as a processor and as a
controller, the purposes of each processing activity, the categories of
recipients, and the applicable retention periods. Customers can request a
summary of the register through the DPO mailbox.

## Who are Aurora Labs' subprocessors?

Subprocessors include the cloud infrastructure provider, the email delivery
service, and the customer support tooling provider. The full, current list is
published at privacy.auroralabs.example/subprocessors and is updated at least
30 days before a new subprocessor is onboarded, giving customers a window to
object as provided in the DPA.

## How does Aurora Labs handle data breaches?

Aurora Labs notifies affected customers without undue delay and no later than
72 hours after confirming a breach affecting personal data. The notification
describes the nature of the breach, the categories and approximate number of
data subjects affected, and the measures taken to mitigate harm. Where the
breach creates a risk to the rights and freedoms of individuals, we also
notify the relevant supervisory authority in accordance with Article 33.

## Does Aurora Labs conduct privacy impact assessments?

Where processing is likely to result in a high risk to individuals, such as
large-scale processing of special category data, Aurora Labs conducts a Data
Protection Impact Assessment (DPIA) before the processing begins. DPIAs are
reviewed by the DPO and refreshed when the processing materially changes.

## Is Aurora Labs SOC 2 certified?

Aurora Labs maintains a SOC 2 Type II report covering security, availability,
and confidentiality. The report is available to customers under an NDA
through the trust center at trust.auroralabs.example. The SOC 2 controls
include access management, change management, incident response, and vendor
management, and they map to the GDPR security obligations in Article 32.

## Does GDPR apply to Aurora Labs' UK customers?

Yes. Aurora Labs complies with the UK GDPR and the Data Protection Act 2018
for customers in the United Kingdom. Transfers from the UK are covered by the
UK International Data Transfer Agreement (IDTA) in addition to the EU
Standard Contractual Clauses.

## Can customers choose a different data residency region later?

Customers can request a region migration through support. Migrations copy the
workspace to the new region and, once verified, delete the source data within
30 days. Migration is not available for workspaces created before the region
feature launched unless the account has fewer than 5,000 documents.

## How long does Aurora Labs keep customer content?

Customer content is deleted 24 months after the end of the subscription term,
matching the retention commitments in the current privacy policy (Version 2).
During the subscription, content is retained for as long as the account is
active. Deleted workspaces are recoverable for 30 days, after which backups
are purged.

## Does Aurora Labs profile users?

Beacon's alerting features rank notifications by relevance based on the
customer's alert configuration and historical alert volume. This ranking is
per-account and does not involve profiling of individuals as defined in
Article 4(4) of the GDPR, and it does not produce legal or similarly
significant effects on data subjects.

## What security measures does Aurora Labs apply?

All data is encrypted in transit with TLS 1.2+ and at rest with AES-256.
Access to production environments requires multi-factor authentication and is
granted on a least-privilege basis. Independent penetration tests are run
quarterly, and all staff complete annual security and privacy training.

## Can data subjects object to processing?

Where we process personal data on the basis of legitimate interest, data
subjects may object under Article 21. We will stop the processing unless we
demonstrate compelling legitimate grounds that override the individual's
interests, rights, and freedoms, or the processing is for the establishment,
exercise, or defense of legal claims.

## Does Aurora Labs offer any additional contractual safeguards?

Beyond the DPA, customers may request a security appendix covering the
technical and organizational measures applied to their data. The security
appendix is incorporated by reference into the DPA and includes the controls
summarized in the SOC 2 report.

## How do I contact Aurora Labs about GDPR questions?

Email dpo@auroralabs.example for questions about the GDPR, the DPA, or data
subject requests. For general privacy questions, use privacy@auroralabs.example.
Our EU representative is Aurora Labs Ireland Ltd, 12 Grand Canal Square,
Dublin 2.

## What records does the DPA cover for audits?

The DPA gives customers audit rights limited to the technical and
organizational measures relevant to their data. Audits are coordinated
through the security team, may be conducted by the customer or an independent
auditor bound by confidentiality, and are subject to a notice period of 30
days. The SOC 2 Type II report satisfies the audit right for most customers,
and a full on-site audit is available to Enterprise customers once per
calendar year at the customer's expense.

## How does Aurora Labs handle special category data?

Special category data (health, biometric, or other sensitive data) is not
supported for processing in the standard service. If a customer identifies a
use case involving special category data, the account is reviewed by the
security and privacy teams, a DPIA is conducted, and the customer must agree
to additional contractual safeguards before processing begins. No special
category data may be uploaded without this review.

## What happens if a customer exports data at termination?

The customer may export workspace content in JSON format at any time and for
60 days after termination. After the export window closes, the workspace is
deleted under the retention schedule in the privacy policy. The export
includes documents, dashboards, alert rules, and query history, but excludes
other users' private messages and system logs.

## Are Aurora Labs' European operations subject to any additional obligations?

Aurora Labs Ireland Ltd is the EU entity for GDPR purposes, and Aurora Labs
Inc. transfers personal data to it under an intra-group agreement that
mirrors the EU Standard Contractual Clauses. The EU entity is responsible
for local regulatory relationships, including the supervision of the
exercise of data subject rights in the EU.

## How are privacy and security responsibilities divided between teams?

The privacy team owns the privacy policy, the DPA, and data subject
requests. The security team owns the technical controls, the SOC 2 report,
and incident response. The DPO bridges the two and reports directly to the
executive team, with an independent reporting line required by Article 38.
Questions about which team owns a specific obligation should be directed to
the DPO mailbox, which routes to the right owner.
