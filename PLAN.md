# General idea
Design a micro service that processes standardized data records from multiple sources, supports aggregation and querying functions and feeds downstream services with relevant information. 


## Assumptions
- Uniqueness of the record is given by the record_id. Had it not been the case, we would have needed to compute an unique hash from the record data.

## Performance requirements
100.000 reqs/hour => ~ 28 req/sec

## Integrity and robustness requirements
[x] - idempotency to prevent double processing of the same record.
[ ] - atomicity to prevent partial processing of the same record.
[x] - retry mechanism.
[ ] - logging & monitoring. TBD

## Scalability requirements
[x] - horizontal scaling. => solved by adding scale to docker compose.
- fault tolerance.
- concurrency control.
- caching.
- rate limiting.
- circuit breaker.
- retries.
- timeouts.

## Functional requirements
### Stages
#### Data ingestion and processing
- Consume input from several services. In our case, choose Redis queue and API ingestion.
- Record format:
```json
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

```
- Process data records.
- Store processed data in a database.

#### Downstream service notifications
- Emit messages to be consumed by the notification service. There should be one message for every record processed. Each message should contain the processed record and a summary of any previous ones for the same destination id and reference.  
- Emit messages to be consumed by alerting service when a record’s value is above a configurable threshold. 

#### Provide aggregated data via API
Start and end time as optional filters. 
- The type of record (positive or negative) as optional filter. 
- Grouping by destination id. The response should include all matching records and a summarized total value per group.

#### Test plan
- Integration tests.
- Load tests.
- Performance tests.