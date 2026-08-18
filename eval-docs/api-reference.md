# Aurora Labs API Reference

REST API documentation for Atlas, Beacon, and Nimbus. Base URL:
`https://api.auroralabs.example/v1`. All requests require an API key sent
as a `Authorization: Bearer` header.

## Authentication

API keys are created in the admin console under Settings > API Keys. Keys
have scopes: `atlas:read`, `atlas:write`, `beacon:read`, `beacon:write`,
`nimbus:read`, `nimbus:write`. Rate limits: 100 requests per minute for
free tier, 1,000 per minute for paid tiers.

Keys are long-lived by default. The security policy requires production
API keys to be rotated every 180 days, and the key management service
revokes keys that exceed the rotation window. For tighter control we
recommend rotating them every 90 days; the audit log records every API key
creation and deletion with the actor's identity. The
`Authorization: Bearer` header must be sent on every request; requests
without a valid key return `401`. Keys with insufficient scope return
`403` with a message describing the required scope.

## Conventions

All request and response bodies are JSON. Timestamps are ISO 8601 strings
with UTC timezone, for example `2025-06-01T12:00:00Z`. IDs are stable
strings: Atlas query IDs look like `aq_2f9c1a`, Beacon alert IDs like
`ba_71d0e3`, Nimbus pipeline IDs like `np_c4a1b9`. Pagination uses
`limit` (default 50, max 500) and `offset` query parameters, and list
endpoints return a `total` field with the unfiltered count. Idempotency
is supported on write endpoints via an `Idempotency-Key` header: replaying
a request with the same key returns the original response without
duplicating the resource.

## Atlas endpoints

### GET /atlas/queries

List saved queries. Returns an array of query objects with `id`, `name`,
`sql`, `owner`, and `updated_at`.

Filters: `owner` (email), `name` (substring match). Example response:

```json
{"total": 1, "queries": [{"id": "aq_2f9c1a", "name": "Revenue by region",
"sql": "SELECT region, sum(revenue) FROM sales GROUP BY region",
"owner": "ada@example.com", "updated_at": "2025-06-01T12:00:00Z"}]}
```

### POST /atlas/queries

Create a saved query. Body: `{"name": string, "sql": string}`. Returns the
created query with a `201` status.

The SQL is validated against the connected warehouse and must reference
tables the workspace can access. A `422` is returned for invalid SQL with
the database error message in the `message` field.

### GET /atlas/queries/{id}

Fetch a saved query by id. Returns the query object, or `404` if it does
not exist.

### DELETE /atlas/queries/{id}

Delete a saved query. Requires `atlas:write` scope. Returns `204` on
success. Deleting a query does not delete dashboards that embed its
results; those dashboards continue to show the last cached result.

### GET /atlas/dashboards/{id}

Fetch a dashboard by id, including its widgets and layout.

### POST /atlas/queries/{id}/run

Execute a saved query and return the result set. Requires `atlas:read`
scope. Query runs are asynchronous for queries expected to take longer
than 30 seconds; the response includes a `run_id` and a `status` of
`running`, and the caller polls `GET /atlas/runs/{run_id}` until the
status is `succeeded` or `failed`.

## Beacon endpoints

### POST /beacon/alerts

Create an alert rule. Body: `{"name": string, "query": string, "threshold":
number, "channels": [string]}`.

The `query` field is a PromQL-style expression evaluated against the
metrics sources connected to the workspace. The `channels` array accepts
`slack`, `email`, `pagerduty`, and webhook URLs. Returns the created rule
with a `201` status.

### GET /beacon/alerts

List alert rules with their enabled state and last-triggered time.

### GET /beacon/alerts/{id}/history

Fetch delivery history for an alert rule. Each entry includes `status`
(delivered, failed, suppressed), `channel`, and `delivered_at`.

### PUT /beacon/alerts/{id}

Update an alert rule. Only the fields provided in the body are changed;
omitted fields keep their current values. Returns the updated rule.

### POST /beacon/alerts/{id}/silence

Silence an alert rule for a duration. Body: `{"until": string}` (ISO 8601)
or `{"duration_minutes": number}`. Silenced rules do not trigger delivery
but continue to record evaluations in the history endpoint.

## Nimbus endpoints

### POST /nimbus/pipelines

Create a pipeline. Body: `{"name": string, "source": string, "sink":
string, "transform": string}`.

The `source` and `sink` fields are connection identifiers created through
the console (for example `kafka://prod-events` and `s3://data-lake/raw`).
The `transform` field is either a named transform from the visual builder
or inline Python for SDK-style pipelines. Returns the created pipeline
with a `201` status and its initial `lag_minutes` of 0.

### GET /nimbus/pipelines

List pipelines with their current status (`running`, `paused`, `failed`)
and lag.

### GET /nimbus/pipelines/{id}/lag

Fetch the current lag in minutes for a pipeline. Returns `{"lag_minutes":
number, "last_event_at": string}`.

### POST /nimbus/pipelines/{id}/replay

Replay pipeline events from a point in time. Body: `{"from": string}` (ISO
8601). Events are re-ingested from the source topic's retained history.
Replays run in parallel with the live pipeline and do not pause ingestion.
Returns a `replay_id` that can be polled via
`GET /nimbus/replays/{replay_id}`.

## Rate limits and headers

Rate limits are enforced per API key, not per workspace. When a limit is
approached, responses include `X-RateLimit-Remaining` and
`X-RateLimit-Reset` headers. Exceeding the limit returns `429` with a
`Retry-After` header. Paid tiers can raise their limits through the admin
console, up to 5,000 requests per minute for Enterprise plans.

## Errors

Errors use standard HTTP status codes: `400` for malformed requests, `401`
for missing or invalid API keys, `403` for scope violations, `404` for
missing resources, `429` for rate limit exceeded, and `500` for server
errors. Error bodies include a `message` field.

Additional codes: `409` for conflicts (for example, creating a pipeline
whose name is already in use), `413` for request bodies over the 10 MB
limit, and `422` for validation failures with a `details` field listing
each invalid field. Retryable errors (`429`, `500`, `503`) should be
retried with exponential backoff; the `Retry-After` header, when present,
takes precedence.

## Webhooks

Beacon can deliver alert events to webhook endpoints you register. The
webhook payload is a JSON object with the alert id, name, severity, the
metric value that triggered it, and a `permalink` to the alert in the
console. Endpoints must respond with `2xx` within 10 seconds; deliveries
that fail are retried with exponential backoff for up to 24 hours, and
delivery attempts are recorded in the alert's history endpoint. Endpoints
are verified at registration by a `GET` challenge containing a random
token that must be echoed back in the response body.

## Pagination details

List endpoints support cursor-based pagination in addition to
`limit`/`offset`. To use cursors, pass `cursor` instead of `offset`; the
response includes a `next_cursor` field that is null on the last page.
Cursor pagination is stable under concurrent writes and is recommended
for lists that change frequently, such as alert history. The `limit`
parameter caps the page size at 500, and requests above the cap are
silently clamped rather than rejected.

## Versioning and deprecation

The API is versioned through the URL path (`/v1`, `/v2`). Additive
changes (new fields, new endpoints) ship without a version bump and are
announced in the changelog. Breaking changes ship in a new version and
are announced at least 90 days before the previous version is frozen;
frozen versions remain available for 12 months. The `Deprecation` and
`Sunset` headers are set on deprecated endpoints. The changelog and
migration guides are published at developers.auroralabs.example.

## Examples and SDKs

Official SDKs are available for Python, TypeScript, and Go, published
under the `auroralabs` namespace on each ecosystem's package registry.
The SDKs handle authentication, retries, and pagination automatically,
and the README of each SDK links to the reference examples: a scheduled
Atlas report export, a Beacon alert with an escalation chain, and a
Nimbus pipeline with a replay. Community SDKs are listed in the
developer portal but are not supported by the Aurora Labs support team.
