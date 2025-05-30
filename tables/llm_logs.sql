CREATE TABLE llm_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP with time zone,
    model_name TEXT NOT null,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    tool_name TEXT
);