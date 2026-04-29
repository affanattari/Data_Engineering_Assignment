# API Main Module
from fastapi import FastAPI, HTTPException
import random
from datetime import datetime

app = FastAPI()

INSTRUMENTS = ["AAPL", "GOOG", "BTC-USD", "ETH-USD"]

def generate_data():
    return {
        "instrument_id": random.choice(INSTRUMENTS),
        "price": round(random.uniform(100, 50000), 2),
        "volume": round(random.uniform(1, 1000), 2),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/v1/market-data")
def get_data():
    # 5% faulty responses
    if random.random() < 0.05:
        if random.choice([True, False]):
            raise HTTPException(status_code=500, detail="Error injected")
        else:
            return [{"instrument_id": "AAPL", "price": "BAD"}]

    return [generate_data() for _ in range(10)]

@app.get("/health")
def health():
    return {"status": "ok"}