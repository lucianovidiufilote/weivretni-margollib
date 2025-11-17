## Setup local venv of python

cd /home/lucian/projects/interview-python-billogram
    python3 -m venv .venv
    source .venv/bin/activate          # or .venv/Scripts/activate on Windows
    pip install --upgrade pip
    pip install -r requirements.txt

Interview assignment - Data processing 
Design a micro service that processes standardized data records from multiple sources, supports aggregation and querying functions and feeds downstream services with relevant information. 
Instructions 
The intended time for this assignment is a maximum of 2 hours. Document your solution in any way you are comfortable with, but be prepared to present it during the interview. The implementation can be in any programming language or even pseudo code. During the interview you will be asked to walk us through it. 
You may choose any tech stack to support the service. Consider quality, scalability and performance. Document the choices and assumptions you make in your design and why. 
Requirements 
1. Consume input from several services. The service should handle about 100,000 messages per hour efficiently. Implement idempotency to prevent duplicate processing, ensuring each record is processed exactly once. The data structure for incoming records is as follows: 
None 
{ 
"recordId": string, 
"time": Datetime, 
"sourceId": string, 
"destinationId": string, 
"type": string ["positive"|"negative"], 
"value": Decimal, 
"unit": string, 
"reference": string, 
} 
2. 
Respond to queries for aggregation. The query and the response should support the
following. 
1. Start and end time as optional filters. 
2. The type of record (positive or negative) as optional filter. 
3. Grouping by destination id. The response should include all matching records and a summarized total value per group. 
3. Emit messages to be consumed by the notification service. There should be one message for every record processed. Each message should contain the processed record and a summary of any previous ones for the same destination id and reference. 
4. Emit messages to be consumed by alerting service when a record’s value is above a configurable threshold. 
Service overview 
DIAGRAM.mermaid shows the intended place for the transactions service in the larger system.

## Quick start

The repository also contains a runnable skeleton for a REST API that exposes a single `/health` endpoint. It is container-first and already wired for PostgreSQL, Redis, and a background worker process so you can iterate on the assignment without spending time on plumbing.

### Stack highlights

- **FastAPI** application server exposed through Uvicorn.
- **PostgreSQL** and **Redis** services provisioned in Docker Compose.
- **RQ**-based worker process backed by Redis for asynchronous tasks.
- **Aggregation worker** that refreshes destination summaries every minute so notification and reporting consumers get near-real-time totals without touching the API path.

### Run locally

```bash
cp .env.example .env                     # adjust if necessary
docker compose up --build
```

The API becomes available at http://localhost:8000/health once the containers have started. A healthy response resembles:

```json
{
  "status": "ok",
  "components": {
    "postgres": {"status": "ok"},
    "redis": {"status": "ok", "detail": "pong=True"}
  }
}
```

Enqueue the bundled demo RQ job from the API container to see the worker execute application code:

```bash
docker compose exec api python -m src.devtools.enqueue_demo
```

### Hot reload during development

Use the dedicated dev compose file to bind-mount the source tree and enable automatic reloads for both the API and worker:

```bash
docker compose -f docker-compose.dev.yaml up --build
```

The dev file defines the same four services (API, worker, Postgres, Redis) as the production compose file but swaps in bind mounts and reload-friendly commands. Any changes to the `src/` directory now trigger FastAPI reloads and restart the worker automatically via `python -m watchfiles --filter python src -- python -m src.worker`.

### Periodic aggregation worker

An auxiliary RQ job (`src.services.aggregation_scheduler.recompute_destination_summaries`) rebuilds destination-level summaries. Every successful record ingestion signals this job, but Redis enforces a configurable cooldown (`AGGREGATION_COOLDOWN_SECONDS`) so recomputes happen at most once per interval regardless of traffic bursts. This keeps the ingestion worker responsive while still providing near-real-time snapshots for APIs and downstream notifications.

## Business endpoints

### Submit a record

The API accepts normalized records via `POST /records` and immediately enqueues them for background processing (idempotent insert, aggregation, and notifications):

```bash
curl -X POST http://localhost:8000/records \
  -H "Content-Type: application/json" \
  -d '{
    "recordId": "rec-001",
    "time": "2024-03-01T12:00:00Z",
    "sourceId": "source-a",
    "destinationId": "dest-123",
    "type": "positive",
    "value": 125.50,
    "unit": "SEK",
    "reference": "invoice-9"
  }'
```

### Query aggregations

Use `GET /records/aggregations` with optional `startTime`, `endTime`, and `type` filters to retrieve the matching records grouped by destination along with each group's running total (positive records add to the total while negative records subtract). Example:

```bash
curl "http://localhost:8000/records/aggregations?startTime=2024-03-01T00:00:00Z&type=positive"
```

### Notifications and alerts

Every processed record emits a notification message (record + the latest cached summary for the same destination/reference) on the `NOTIFICATION_CHANNEL`. The cached summary is refreshed asynchronously by the aggregation worker discussed above, so downstream consumers receive near-real-time totals without impacting ingestion latency. When a single record's `value` is above the configurable `ALERT_THRESHOLD`, the service also publishes an alert on `ALERT_CHANNEL`. Both channels are backed by Redis `PUBLISH` so downstream services can subscribe without coupling to the API.

### Next steps

- Harden the storage layer with migrations and data retention policies.
- Expand automated tests (unit + integration) that cover the worker pipeline and aggregation endpoint.
- Integrate real downstream consumers for the Redis notification/alert channels or adapt them to your messaging system of choice.
