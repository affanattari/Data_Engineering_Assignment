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

## Scaling Strategy

For handling 1B+ events/day:

* Kafka for streaming ingestion
* Spark/Flink for distributed processing
* Data Lake (S3 + Parquet)
* Partitioning by time and instrument

---

## Monitoring

* Health endpoints (`/health`)
* Logging for processed/dropped records
* Can integrate Prometheus + Grafana for metrics

---

## Idempotency

* Composite primary key `(instrument_id, timestamp)`
* `ON CONFLICT DO NOTHING`
* Ensures no duplicate or partial data

