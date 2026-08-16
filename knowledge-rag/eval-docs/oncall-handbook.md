# Aurora Labs On-Call Handbook

Everything you need to know about being on call for the Aurora Labs
platform: Atlas, Beacon, and Nimbus.

## What being on call means

Each engineer is scheduled for a one-week primary rotation, with a secondary
engineer on backup. During your week you are the first responder for pages
between 9:00 and 18:00 local time; overnight and weekend pages go to the
rotating secondary unless you opt in.

## Response expectations

SEV1 pages must be acknowledged within 5 minutes. SEV2 within 15 minutes.
If you cannot respond, use the swap tool to find a replacement at least
24 hours before your shift starts.

## Shift handoff

At the end of your shift, write a handoff summary covering: open incidents,
known issues, and anything the next engineer should watch. Post it in the
#incidents channel and tag the incoming on-call engineer.

## Tools

- Paging: PagerDuty, schedule "prod-primary" and "prod-secondary"
- War rooms: Google Meet, linked from the #incidents channel
- Status page: status.auroralabs.example, updated by the communications lead

## Incident commander role

The incident commander (IC) is the single decision-maker during an incident.
The IC decides severity, approves mitigations, and runs the post-incident
review. The IC is usually the most senior engineer present, not necessarily
the on-call responder.

## Tips

Always pull the latest runbook before debugging. Document what you tried in
the incident thread — future engineers will thank you. Take breaks: for
incidents longer than 4 hours, the IC should rotate the war-room lead.
