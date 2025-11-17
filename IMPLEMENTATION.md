# Ingestion
The system can ingest data from two sources

**API call**
```shell
curl --location 'http://localhost:8000/records' \
--header 'Content-Type: application/json' \
--data '{
    "recordId": "12541",
    "time": "2025-11-17 15:00:00",
    "sourceId": "214",
    "destinationId": "bgvgb343qg",
    "type": "positive",
    "value": 123.20,
    "unit": "SEK",
    "reference": "2309875t923hfgiu"
}'
```
*After validation, this queues the record for processing.

**Redis queue** 
```shell
redis-cli LPUSH src.jobs.records.process_record '{
    "recordId": "12541",
    "time": "2025-11-17 15:00:00",
    "sourceId": "214",
    "destinationId": "bgvgb343qg",
    "type": "positive",
    "value": 123.20,
    "unit": "SEK",
    "reference": "2309875t923hfgiu"
}' 
```

The worker consumes the queue.
Field `records.record_id` is a unique identifier for the record. If it exists in the database, it is ignored.
If it does not exist, it is inserted into the database. The notification service and alerting service are notified.
Retry mechanism is in place, using basic RQ functionality. After 3 retries, the record is marked as failed and is kept into FailedJobRegistry. We can later decide what to do with it: a) retry b) delete c) fix underlying issue and retry.