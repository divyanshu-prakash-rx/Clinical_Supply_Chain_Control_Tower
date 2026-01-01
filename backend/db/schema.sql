CREATE TABLE IF NOT EXISTS ai_decisions (
    id SERIAL PRIMARY KEY,
    decision_json JSONB NOT NULL,
    decision_type VARCHAR(50),
    source_tables JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_decisions_timestamp ON ai_decisions(timestamp DESC);
CREATE INDEX idx_ai_decisions_type ON ai_decisions(decision_type);
