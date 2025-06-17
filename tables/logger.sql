CREATE TABLE app_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    logger_name TEXT,
    module TEXT,
    function TEXT,
    line_number INT
);