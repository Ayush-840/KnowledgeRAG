# Aurora Labs On-Call Handbook

Everything you need to know about being on call for the Aurora Labs
platform: Atlas, Beacon, and Nimbus.

## What being on call means

Each engineer is scheduled for a one-week primary rotation, with a secondary
engineer on backup. During your week you are the first responder for pages
between 9:00 and 18:00 local time; overnight and weekend pages go to the
rotating secondary unless you opt in.

The primary is responsible for acknowledging pages and starting the incident
process from the runbook. The secondary is the first person the primary
escalates to and is expected to be reachable but not necessarily at a desk.
Both roles are tracked in the "prod-primary" and "prod-secondary" PagerDuty
schedules. Schedules are published 6 weeks in advance, and every engineer is
expected to review them for conflicts with holidays and planned time off.

## Response expectations

SEV1 pages must be acknowledged within 5 minutes. SEV2 within 15 minutes.
If you cannot respond, use the swap tool to find a replacement at least
24 hours before your shift starts.

Acknowledging a page means confirming it in the paging tool and joining the
#incidents channel; it does not mean the issue is resolved. If you are
driving, in a meeting, or otherwise unable to work on the incident, still
acknowledge and then immediately escalate to the secondary. It is far worse
to let a page time out than to escalate early. Unacknowledged pages
escalate automatically every 5 minutes up the chain.

## Shift handoff

At the end of your shift, write a handoff summary covering: open incidents,
known issues, and anything the next engineer should watch. Post it in the
#incidents channel and tag the incoming on-call engineer.

A good handoff includes: the current status of any open incidents, any
mitigations applied that may need follow-up, alerts that fired during the
shift but turned out to be benign (so the next engineer does not re-investigate
them), and a short list of "things to watch". Handoffs should be written in
the last hour of the shift, while the details are still fresh, and the
incoming primary is expected to read them before their shift starts.

## Tools

- Paging: PagerDuty, schedule "prod-primary" and "prod-secondary"
- War rooms: Google Meet, linked from the #incidents channel
- Status page: status.auroralabs.example, updated by the communications lead

Supporting tools: the on-call dashboard at oncall.auroralabs.example shows
current alert volume, pipeline lag, and open incident count; Grafana
dashboards for each service are linked from the on-call dashboard. The
runbook and this handbook are both linked from the dashboard header.

## Incident commander role

The incident commander (IC) is the single decision-maker during an incident.
The IC decides severity, approves mitigations, and runs the post-incident
review. The IC is usually the most senior engineer present, not necessarily
the on-call responder.

The IC is assigned from the engineering leadership rotation, not from the
on-call rotation, so the responder can focus on the technical investigation.
If no IC is available, the primary on-call engineer assumes the role and
hands it off as soon as a leadership engineer joins. The IC's decisions bind
the war room, including the decision to roll back a deployment or fail over
a region.

## Severity decisions in practice

Deciding severity quickly is a skill. Use the decision aid in the runbook:
SEV1 for total outage or data loss, SEV2 for significant degradation to a
subset of customers, SEV3 for minor issues with a workaround, SEV4 for
cosmetic. When the situation is ambiguous, ask one question: "would a
reasonable customer notice this within the next hour?" If yes, treat it as
SEV2 or higher.

## Communicating during incidents

The communications lead owns external updates; you should not post status
page updates yourself unless you are the communications lead. In the
#incidents channel, post a short update every time you finish a meaningful
action — what you tried and what the effect was — so the scribe can record
it. Avoid long silences: if you are investigating for more than 15 minutes
without an update, post a one-line status so the war room knows you are still
working.

## Common pitfalls

- Debugging before declaring. Always declare the incident and assign roles
  first; the five-minute checklist exists because it saves time overall.
- Scope creep. Fix the incident, then file tickets for everything else you
  notice. A SEV1 is not the time to also refactor the alerting rules.
- Solo heroics. The secondary exists to help; page them early when the
  investigation stalls.
- Forgetting the customer. The status page update within 15 minutes is not
  optional, even if the cause is still unknown.
- Skipping the handoff. The next engineer inherits your shift's context;
  a written handoff is the difference between a calm week and a fire drill.

## Training and readiness

Before your first on-call shift, complete the on-call training module and
read the runbook cover to cover. Every engineer participates in at least one
quarterly game day, where synthetic incidents are injected into staging.
New engineers shadow a senior engineer for one full week before carrying the
primary pager. After each of your first three incidents, have the IC walk
you through the post-incident review so you learn the patterns.

## Well-being

On-call weeks are intense. Aurora Labs caps primary on-call at one week in
every six, and you must take at least one full day off after a week with a
SEV1 or SEV2 incident. If an incident runs past 4 hours, the IC rotates the
war-room lead so no one carries the shift alone. If you feel burned out,
talk to your manager — being unavailable for a rotation is always preferable
to being unsafe on call.

## Tips

Always pull the latest runbook before debugging. Document what you tried in
the incident thread — future engineers will thank you. Take breaks: for
incidents longer than 4 hours, the IC should rotate the war-room lead.

## First week checklist

Your first on-call week is about learning the platform, not about being
the hero. Before your first shift, complete these steps: read the runbook
cover to cover, skim the last three post-incident reviews in the shared
drive, subscribe to the #incidents channel and the on-call dashboard,
verify you receive PagerDuty test pages, and shadow a senior engineer for
at least one incident (real or from a game day). During your first week,
pair with the secondary on any page before acting, and ask the IC for a
walkthrough after your first incident.

## Regional rotation coverage

Aurora Labs operates in three regions: us-east-1, eu-central-1, and
ap-southeast-2. Incidents in each region are handled by the on-call
rotation closest to that region's business hours. The primary in the
affected region owns the incident; engineers in other regions join as
support. If the affected region's primary is asleep, the global
secondary covers until the region's business hours resume. The on-call
dashboard shows which rotation is active for each region and the current
handoff time.

## Communication escalation for executives

For SEV1 incidents lasting more than 2 hours, the on-call manager sends
a summary to the executive team every 2 hours. The summary includes the
incident name, current severity, customer impact, and the next planned
mitigation step. The communications lead prepares these summaries from
the incident timeline; the IC approves them. If the incident affects a
top-tier customer, the customer success manager opens a thread in the
support portal before the executive summary goes out.

## Learning from incidents

Every engineer is expected to attend at least two post-incident reviews
per quarter, either as a participant or as an observer. The reviews are
blameless: the focus is on the system, the process, and the decisions
that led to the incident, not on the individuals involved. The most
valuable contributions to a review are data points from the timeline
and suggestions for detection improvements, since detection gaps are the
most common corrective action category in the review database.
