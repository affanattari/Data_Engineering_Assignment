# End-to-End Data Engineering Pipeline

## Overview
I built an end-to-end data pipeline where a FastAPI service simulates real-time market data with fault injection. The ETL pipeline extracts data with retry and exponential backoff, validates it using Pydantic, computes VWAP, and detects outliers for data quality. The processed data is batch inserted into PostgreSQL with idempotency ensured using a composite primary key. The entire system is containerized using Docker for reproducibility.

---

## Architecture

FastAPI (Data Source) → ETL Pipeline (Processing Layer) → PostgreSQL (Storage Layer)

        ┌────────────────────┐
        │     FastAPI        │
        │  (Data Source)     │
        └─────────┬──────────┘
                  │ REST API
                  ▼
        ┌────────────────────┐
        │      ETL           │
        │ Validation + VWAP  │
        │ Outlier Detection  │
        └─────────┬──────────┘
                  │ Batch Insert
                  ▼
        ┌────────────────────┐
        │   PostgreSQL       │
        │   (Data Storage)   │
        └────────────────────┘

---

## Components

### 1. FastAPI (Source)

* Generates synthetic market data
* Simulates real-world failures using fault injection (5%)
* Endpoint: `/v1/market-data`

### 2. ETL Pipeline

* Extracts data from API with retry + exponential backoff
* Validates schema using Pydantic
* Computes VWAP (Volume Weighted Average Price)
* Detects outliers (>15% deviation)
* Batch inserts into database
* Ensures idempotency using composite primary key

### 3. PostgreSQL (Sink)

* Stores processed and validated data
* Prevents duplicate records using `(instrument_id, timestamp)` as primary key

---

## Features

* Fault-tolerant API ingestion
* Schema validation (Pydantic)
* Retry mechanism with exponential backoff
* Batch database writes for performance
* Outlier detection for data quality
* Structured logging for observability
* Fully containerized using Docker

---

## 🐳 Setup & Run

```bash
docker-compose up --build
```

---

## 🔍 Sample Output

```sql
SELECT * FROM market_data;
```

| instrument_id | price | volume | timestamp | is_outlier |
| ------------- | ----- | ------ | --------- | ---------- |
| AAPL          | 150.5 | 10     | ...       | false      |
| BTC-USD       | 40000 | 2      | ...       | true       |

---

## Scaling: How would your architecture change if the data volume increased to 1 billion events per day? (e.g., Kafka, Spark, or Cloud-native tools).

At this scale, the current setup (API + ETL + single database) won’t handle the load. So we redesign it:
* Add Apache Kafka between API and ETL to handle high data volume. Data is split into partitions (e.g., by instrument), which allows parallel processing.
* Replace simple polling with Apache Spark Structured Streaming or Apache Flink to process data in real-time with built-in fault tolerance.
* Store data in layers:  
Hot data → fast databases like ClickHouse/TimescaleDB  
Cold data → cloud storage like S3 (for analytics)  
* Use a schema registry to validate data format before processing.
* Deduplication is handled earlier in the pipeline using streaming guarantees (exactly-once processing).

---

## Monitoring: How would you implement "Health Checks" to ensure the pipeline is running correctly in a production environment?

We monitor the pipeline at 3 levels:
* Pipeline heartbeat:- Track the last successful run time. If the pipeline hasn’t run for a while → trigger alert.
* Data freshness check:- Query latest record timestamp from DB. If data is not updating → pipeline is stuck.
* Data quality check:- Monitor how many records fail validation. Sudden spike → upstream data issue.
* Additionally:- We can Use dashboards (e.g., Grafana) to monitor CPU, memory, DB connections.

---

## Recovery: If the pipeline fails midway through a 10GB batch, how do you ensure "Idempotency" (no partial or duplicate data)?

We ensure no duplicate or partial data even if the pipeline fails:
* Database-level safety:- Use ON CONFLICT DO NOTHING with a composite key → prevents duplicates.
* Batch tracking (checkpointing):  
Before processing → mark batch as in_progress  
After success → mark as complete  
On restart → retry incomplete batches  
* Transactional inserts:- Each batch runs in a single transaction → either fully inserted or not at all.
* Offset tracking (if supported):- Store last processed offset → resume from where it failed.

