# Aurora Labs Platform Architecture — Part 1: Design

*Internal engineering report. Authors: R. Chen, A. Okafor. Part 2 covers
benchmarks; read both parts together.*

## Overview

This report describes the architecture of the Aurora Labs platform as of
2025. The platform consists of three main components: the **query engine**
(internal codename "Calcite"), the **stream processor** (codename "Kestrel"),
and the **catalog service** (codename "Marina").

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

## Stream processor (Kestrel)

Kestrel is the stream processor behind Nimbus. It consumes events from
Kafka, applies transforms written in the visual builder or the Python SDK,
and writes to sinks. Kestrel guarantees exactly-once semantics via
transactional offsets and idempotent sink writes.

Key design decisions:
- State stored in a replicated RocksDB-backed store
- Automatic schema drift detection with configurable fail modes
- Backpressure via Kafka consumer group lag monitoring

## Catalog service (Marina)

Marina is the metadata catalog shared by Atlas and Nimbus. It stores table
schemas, pipeline definitions, access policies, and data lineage. Marina is
a strongly consistent service backed by a replicated log.

Key design decisions:
- All mutations go through a single writer with a replicated log
- Read replicas serve query planning at low latency
- Access control enforced at the catalog, not the engine

## Deployment model

The platform runs on Kubernetes in three regions: us-east-1, eu-central-1,
and ap-southeast-2. Each region runs the full stack; there is no global
dependency between regions.
