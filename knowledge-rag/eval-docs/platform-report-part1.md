# Aurora Labs Platform Architecture — Part 1: Design

*Internal engineering report. Authors: R. Chen, A. Okafor. Part 2 covers
benchmarks; read both parts together.*

## Overview

This report describes the architecture of the Aurora Labs platform as of
2025. The platform consists of three main components: the **query engine**
(internal codename "Calcite"), the **stream processor** (codename "Kestrel"),
and the **catalog service** (codename "Marina").

This part covers the design and the rationale behind the key decisions.
Part 2 (platform-report-part2.md) reports benchmark results for the same
three components on the reference cluster. Cross-references between the two
parts are marked with the part number so the reader can jump between design
and measured behavior.

## Query engine (Calcite)

Calcite is the SQL engine that powers Atlas. It parses and optimizes queries,
then executes them against customer data sources. Calcite uses a cost-based
optimizer with rule-based rewrites and a vectorized execution engine. Queries
are executed in a distributed fashion: a coordinator node plans the query
and worker nodes execute fragments in parallel.

Key design decisions:
- Columnar in-memory execution for analytical workloads
- Predicate pushdown to source systems wherever possible
- A connector framework supporting Snowflake, BigQuery, Postgres, and S3

The optimizer pipeline has four stages: parsing into an AST, logical
planning with rule-based rewrites (predicate pushdown, filter/join
reordering, projection pruning), cost-based physical planning where the
planner enumerates join orders and selects the cheapest via estimated row
cardinalities, and finally code generation into the vectorized execution
engine. Cardinality estimates come from Marina's statistics service, which
periodically samples tables so the planner does not rely on stale row
counts.

Execution is divided into stages that map to worker nodes. The coordinator
performs a dynamic partition of the data and schedules stages as they
become runnable. Intermediate results are shuffled over TCP with
compression, and spill-to-disk is supported for joins and aggregations
that exceed worker memory. The connector framework abstracts the
differences between sources: pushdown-capable connectors (Snowflake,
BigQuery) receive as much of the predicate and projection as possible,
while the Postgres connector falls back to full-scan with local filtering
for complex queries.

## Stream processor (Kestrel)

Kestrel is the stream processor behind Nimbus. It consumes events from
Kafka, applies transforms written in the visual builder or the Python SDK,
and writes to sinks. Kestrel guarantees exactly-once semantics via
transactional offsets and idempotent sink writes.

Key design decisions:
- State stored in a replicated RocksDB-backed store
- Automatic schema drift detection with configurable fail modes
- Backpressure via Kafka consumer group lag monitoring

The core of Kestrel is a topology of operators: source operators consume
from Kafka topics, transform operators apply the user's logic, and sink
operators write to the destination. Stateful operators (windows,
aggregations, deduplication) keep state in a replicated RocksDB-backed
store, so a worker failure does not lose state. Exactly-once is achieved by
committing Kafka offsets transactionally together with the state store, and
by making sink writes idempotent (for example, S3 writes use deterministic
object keys).

Schema drift is detected when an event arrives whose schema differs from
the one registered in Marina. The configured fail mode decides the
behavior: `add` (add new fields to the target schema), `quarantine` (route
the event to a quarantine topic for review), or `fail` (stop the pipeline
and page the owner). The default is `add` for additive changes and
`quarantine` for breaking changes.

## Catalog service (Marina)

Marina is the metadata catalog shared by Atlas and Nimbus. It stores table
schemas, pipeline definitions, access policies, and data lineage. Marina is
a strongly consistent service backed by a replicated log.

Key design decisions:
- All mutations go through a single writer with a replicated log
- Read replicas serve query planning at low latency
- Access control enforced at the catalog, not the engine

Marina's data model is organized around objects (tables, pipelines,
policies) with versioned metadata. Every mutation is appended to a
replicated log; the single writer applies the log to the object store, and
read replicas tail the log to serve reads. This gives strong consistency
for writes while keeping read latency low for query planning, which is the
hot path. Lineage is recorded as edges between objects, so a dashboard can
trace back to the tables and pipelines that feed it.

Access control is enforced centrally in Marina: when a user runs a query,
Calcite asks Marina for the access policy for the tables involved, and
row-level security filters are pushed into the execution plan. This is a
deliberate design choice — enforcing at the catalog means a policy change
takes effect everywhere immediately, instead of waiting for each engine to
pick it up.

## Deployment model

The platform runs on Kubernetes in three regions: us-east-1, eu-central-1,
and ap-southeast-2. Each region runs the full stack; there is no global
dependency between regions.

Each region is self-contained: a deployment of Calcite, Kestrel, and
Marina, with its own Kafka cluster and object storage. Customers are
pinned to the region selected at workspace creation. Cross-region
replication exists only for customer data residency requirements and for
disaster recovery, where the replicated log of Marina provides the
recovery point. The control plane (console, billing, identity) runs as a
global service in us-east-1 with read replicas in the other regions; a
control-plane outage does not affect data-plane query and pipeline
processing.

## Failure handling

The design assumes components fail. Calcite coordinator failover is
handled by a leader election backed by Marina; in-flight queries are
restarted by the new leader. Kestrel worker failure recovers from the
replicated state store, and the exactly-once mechanism ensures no event is
lost or duplicated. Marina itself is replicated with a majority quorum, so
a minority of replica failures does not affect availability. The
degradation behavior of each component under load is measured in Part 2,
which reports the benchmark results that validate these design choices.

## Authentication and authorization

The platform uses a single identity layer for all three products. Users
authenticate through the console using SSO (SAML or OIDC) or email and
password with mandatory multi-factor authentication for administrative
roles. Tokens are short-lived JWTs with a 15-minute lifetime, refreshed
through a rotating refresh token. Authorization is policy-based: Marina
stores access policies, and each service evaluates them at request time.
This means a policy change takes effect immediately, without waiting for
service-side caches to expire.

## Observability

The platform emits structured logs, metrics, and traces from every
component. Calcite logs each query with its plan shape and stage timings;
Kestrel logs each event batch with processing latency; Marina logs every
mutation. Metrics feed the Beacon alerting service, which is how the
on-call runbook detects the failure modes it describes. Traces are
collected with a 1% sampling rate under normal operation and 100% during
incidents. Log retention is 30 days for verbose logs and 12 months for
audit-relevant events.

## Capacity planning

Capacity is planned against the reference numbers in Part 2. Each Calcite
worker handles roughly 8 concurrent queries; each Kestrel worker handles
approximately 42,000 events per second per partition before state-store
serialization becomes the bottleneck; Marina read replicas serve planning
lookups at 2.3 ms p95 up to 5 million catalog objects. The deployment in
Part 2 (24 workers) sustains the reference workloads with at least 2x
headroom, which is the planning target for all services. Autoscaling is
enabled for Calcite workers and Kestrel workers based on queue depth, with
cooldown periods to avoid oscillation.

## Roadmap implications

Part 2 identifies three optimization targets: the Calcite coordinator
scheduler, Kestrel's per-partition state-store writes, and Marina's index
at extreme catalog sizes. Part 1's design notes that the coordinator was
kept single-writer for correctness in the initial launch, and that
sharding it is the natural next step because all state it needs is
already in Marina. The state-store bottleneck is a known tradeoff of the
replicated RocksDB design: replication adds write amplification, which the
2025 H2 work addresses with batched state merges.
