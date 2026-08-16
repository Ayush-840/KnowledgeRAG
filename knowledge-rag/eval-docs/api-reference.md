# Aurora Labs API Reference

REST API documentation for Atlas, Beacon, and Nimbus. Base URL:
`https://api.auroralabs.example/v1`. All requests require an API key sent
as a `Authorization: Bearer` header.

## Authentication

API keys are created in the admin console under Settings > API Keys. Keys
have scopes: `atlas:read`, `atlas:write`, `beacon:read`, `beacon:write`,
`nimbus:read`, `nimbus:write`. Rate limits: 100 requests per minute for
free tier, 1,000 per minute for paid tiers.

## Atlas endpoints

### GET /atlas/queries

List saved queries. Returns an array of query objects with `id`, `name`,
`sql`, `owner`, and `updated_at`.

### POST /atlas/queries

Create a saved query. Body: `{"name": string, "sql": string}`. Returns the
created query with a `201` status.

### GET /atlas/dashboards/{id}

Fetch a dashboard by id, including its widgets and layout.

## Beacon endpoints

### POST /beacon/alerts

Create an alert rule. Body: `{"name": string, "query": string, "threshold":
number, "channels": [string]}`.

### GET /beacon/alerts/{id}/history

Fetch delivery history for an alert rule. Each entry includes `status`
(delivered, failed, suppressed), `channel`, and `delivered_at`.

## Nimbus endpoints

### POST /nimbus/pipelines

Create a pipeline. Body: `{"name": string, "source": string, "sink":
string, "transform": string}`.

### GET /nimbus/pipelines/{id}/lag

Fetch the current lag in minutes for a pipeline. Returns `{"lag_minutes":
number, "last_event_at": string}`.

## Errors

Errors use standard HTTP status codes: `400` for malformed requests, `401`
for missing or invalid API keys, `403` for scope violations, `404` for
missing resources, `429` for rate limit exceeded, and `500` for server
errors. Error bodies include a `message` field.
