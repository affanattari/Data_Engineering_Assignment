-- Database initialization script
CREATE TABLE IF NOT EXISTS market_data (
    instrument_id TEXT,
    price FLOAT,
    volume FLOAT,
    timestamp TIMESTAMP,
    is_outlier BOOLEAN,
    PRIMARY KEY (instrument_id, timestamp)
);