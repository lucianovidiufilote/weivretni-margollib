# Design Summary

## Components

| Component | Responsibility |
|-----------|----------------|
| **FastAPI** (`src/main.py`, `src/api/records.py`) | Validates incoming records and pushes them to the Kafka topic `records.in`. Serves the aggregation endpoint directly from PostgreSQL. |
| **PostgreSQL** | Stores raw records, per-destination aggregates, and the outbox table used for reliable messaging. Schema is defined in `db/init.sql`. |
| **Kafka** | Transports records in, and broadcasts notification/alert events out. |
| **Ingestion worker** (`src/workers/ingestion.py`) | Consumes `records.in`, writes records and aggregates inside a single DB transaction, and emits notification/alert rows into the `outbox` table (outbox pattern). |
| **Outbox worker** (`src/workers/outbox_dispatcher.py`) | Polls the `outbox` table using `FOR UPDATE SKIP LOCKED`, publishes each payload to Kafka, and marks rows as published. |

## Data flow

1. Client POSTs `/records`.
2. API validates the payload and pushes it to Kafka (`records.in`). Response is immediate (`202`).
3. The ingestion worker:
   - Inserts the record (`ON CONFLICT DO NOTHING` handles idempotency).
   - Upserts the `(destinationId, reference)` aggregate (running total + count).
   - Stores a notification payload in `outbox` (`type=notification`, destination=`notifications`).
   - Optionally stores an alert payload in `outbox` if the record value passes the configured threshold.
4. The outbox worker publishes those rows to Kafka (`notifications` / `alerts`) and stamps `published_at`.
5. `/records/aggregations` queries `records` with optional `startTime`, `endTime`, and `type` filters, grouping by `destinationId`.

## Schema

Defined once in `db/init.sql`. Core tables:

```
records(record_id PK, time, source_id, destination_id, type, value, unit, reference, processed_at)
aggregates(destination_id PK, reference PK, total_value, record_count, last_record_id, last_time)
thresholds(destination_id, reference, unit, threshold)           -- optional future overrides
outbox(id UUID PK, event_type, destination, payload JSONB, created_at, published_at, retries)
```

Indexes support the aggregation filters (`time`, `destination_id`, `type`).

## Reliability

- **Idempotency**: enforced by `records.record_id` primary key.
- **Atomicity**: record insert, aggregate update, and outbox inserts run in a single transaction.
- **Outbox pattern**: guarantees we never notify without having written the record, and Kafka publishes exactly once per outbox row.
- **Back-pressure**: if Kafka is down, the outbox table buffers events until the dispatcher catches up.

## Queries

```
GET /records/aggregations?startTime=&endTime=&type=
```

Runs a single SQL statement:

```sql
SELECT destination_id,
       jsonb_agg(jsonb_build_object(... ORDER BY time)) AS records,
       SUM(CASE WHEN type = 'positive' THEN value ELSE -value END) AS total_value
FROM records
WHERE ($1 IS NULL OR time >= $1)
  AND ($2 IS NULL OR time <= $2)
  AND ($3 IS NULL OR type = $3)
GROUP BY destination_id;
```

This satisfies the requirement to return all matching records and the summarized total per destination.
