# Aurora Labs Platform Architecture — Part 2: Benchmarks

*Internal engineering report. Authors: A. Okafor, R. Chen. Read together
with Part 1, which describes the components benchmarked here.*

## Methodology

All benchmarks were run on the reference cluster described in Part 1
(Kubernetes, us-east-1, m6i.4xlarge workers). Each test was run three
times; the median is reported. Workloads are representative of customer
patterns from the Atlas and Nimbus product telemetry.

## Calcite (query engine) results

The Calcite query engine benchmark used a 1 TB TPC-H dataset at scale
factor 1000.

- Cold query p95 latency: 4.1 seconds
- Warm query p95 latency: 1.8 seconds
- Throughput: 120 concurrent queries sustained
- Join-heavy queries (Q9, Q21): p95 5.6 seconds cold

Calcite meets the Atlas p95 latency target of 2 seconds only for warm
queries; cold queries exceed it by roughly 2x.

## Kestrel (stream processor) results

The Kestrel benchmark used a synthetic clickstream with 50,000 events per
second.

- End-to-end processing latency p95: 210 milliseconds
- Throughput ceiling: 250,000 events per second per cluster
- Backpressure onset: 32 minutes of consumer group lag
- Exactly-once overhead: 12% vs at-least-once baseline

Kestrel comfortably handles the Nimbus 30-minute lag commitment at 5x the
reference load.

## Marina (catalog service) results

- Write p95 latency: 14 milliseconds
- Read p95 latency: 2.3 milliseconds from read replicas
- Maximum catalog size tested: 5 million objects

## Discussion

The two components with headroom concerns are Calcite cold queries and
Marina at extreme catalog sizes. Both are scheduled for optimization in the
2025 H2 roadmap. Overall, the platform meets or exceeds its published SLA
targets at reference load.
