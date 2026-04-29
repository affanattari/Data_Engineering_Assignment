import requests
import psycopg2
from psycopg2.extras import execute_batch
from pydantic import BaseModel, ValidationError
from datetime import datetime
from collections import defaultdict
import time
import logging

# ---------------- CONFIG ---------------- #
API_URL = "http://api:8000/v1/market-data"

DB_CONFIG = {
    "host": "db",
    "database": "market",
    "user": "postgres",
    "password": "postgres"
}

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- MODEL ---------------- #
class MarketData(BaseModel):
    instrument_id: str
    price: float
    volume: float
    timestamp: datetime

# ---------------- FETCH WITH RETRY ---------------- #
def fetch_data(retries=3):
    for attempt in range(retries):
        try:
            res = requests.get(API_URL, timeout=5)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            logging.warning(f"[Retry {attempt+1}] API failed: {e}")
            time.sleep(2 ** attempt)  # exponential backoff
    return []

# ---------------- VALIDATION ---------------- #
def validate_data(raw_data):
    valid = []
    dropped = 0

    for record in raw_data:
        try:
            valid.append(MarketData(**record))
        except ValidationError:
            dropped += 1

    return valid, dropped

# ---------------- VWAP ---------------- #
def calculate_vwap(data):
    grouped = defaultdict(list)

    for d in data:
        grouped[d.instrument_id].append(d)

    vwap = {}
    for inst, records in grouped.items():
        total_pv = sum(x.price * x.volume for x in records)
        total_vol = sum(x.volume for x in records)
        vwap[inst] = total_pv / total_vol if total_vol else 0

    return vwap

# ---------------- OUTLIER DETECTION ---------------- #
def mark_outliers(data, vwap):
    rows = []

    for d in data:
        avg = vwap[d.instrument_id]
        is_outlier = abs(d.price - avg) / avg > 0.15 if avg else False

        rows.append((
            d.instrument_id,
            d.price,
            d.volume,
            d.timestamp,
            is_outlier
        ))

    return rows

# ---------------- DB CONNECTION ---------------- #
def connect_db():
    return psycopg2.connect(**DB_CONFIG)

# ---------------- BATCH INSERT ---------------- #
def insert_batch(conn, rows):
    cur = conn.cursor()

    query = """
    INSERT INTO market_data (instrument_id, price, volume, timestamp, is_outlier)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
    """

    execute_batch(cur, query, rows)

    conn.commit()
    cur.close()

# ---------------- MAIN PIPELINE ---------------- #
def run():
    logging.info("ETL Pipeline started...")

    while True:
        start_time = time.time()

        # Step 1: Extract
        raw_data = fetch_data()

        # Step 2: Validate
        valid_data, dropped = validate_data(raw_data)

        if not valid_data:
            logging.warning("No valid data received. Skipping cycle.")
            time.sleep(5)
            continue

        # Step 3: Transform
        vwap = calculate_vwap(valid_data)
        rows = mark_outliers(valid_data, vwap)

        # Step 4: Load
        try:
            conn = connect_db()
            insert_batch(conn, rows)
            conn.close()
        except Exception as e:
            logging.error(f"DB Insert failed: {e}")
            time.sleep(5)
            continue

        # Step 5: Logging
        logging.info(
            f"Processed={len(rows)}, Dropped={dropped}, Time={round(time.time() - start_time, 2)}s"
        )

        # Step 6: Wait before next batch
        time.sleep(5)

# ---------------- ENTRY POINT ---------------- #
if __name__ == "__main__":
    run()