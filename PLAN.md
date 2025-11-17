# General idea
Design a micro service that processes standardized data records from multiple sources, supports aggregation and querying functions and feeds downstream services with relevant information. 

## Assumptions
- Uniqueness of the record is given by the record_id. Had it not been the case, we would have needed to compute an unique hash from the record data.

## Performance requirements
100.000 reqs/hour => ~ 28 req/sec

## Integrity and robustness requirements
- **Idempotency**: enforced by `records.record_id` primary key and `ON CONFLICT DO NOTHING`.
- **Atomicity**: ingestion worker inserts records, updates aggregates, and writes outbox events inside a single DB transaction.
- **At-least-once notifications**: outbox table buffers events; dispatcher retries until Kafka publishes succeed.

## Functional stages
1. **Ingestion**: API validates and publishes to Kafka (`records.in`). Worker consumes, writes to Postgres, and emits outbox events.
2. **Notifications/alerts**: Outbox dispatcher publishes to Kafka topics (`notifications`, `alerts`) exactly once.
3. **Query**: FastAPI aggregations endpoint reads directly from `records` with optional time/type filters and groups by destinationId, returning both the records and the per-destination total.

## Pending work
- Logging/metrics for workers.
- Automated tests for ingestion/outbox logic.
