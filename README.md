# Clinical Supply Chain Control Tower 
## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Running the Application](#running-the-application)
8. [Testing](#testing)
9. [API Documentation](#api-documentation)
10. [Agent Details](#agent-details)
11. [Troubleshooting](#troubleshooting)

## Project Overview

The Clinical Supply Chain Control Tower is a multi-agent AI system designed to autonomously monitor and analyze clinical supply chain risks. It addresses two critical problems:

1. Reactive management leading to stock-outs during enrollment spikes
2. High-value drug batches expiring unused

### Key Features

- Multi-agent architecture with specialized domain agents
- Real-time inventory and demand analysis
- Regulatory compliance checking
- Logistics and shipping timeline validation
- Quality assurance and stability monitoring
- Auditable decision logging
- RESTful API for integration

## Architecture

```
backend/
├── agents/
│   ├── router_agent.py              # Intent classification & orchestration
│   ├── inventory_agent.py           # Stock & expiry detection
│   ├── demand_agent.py              # Enrollment velocity forecasting
│   ├── logistics_agent.py           # Shipping timeline validation
│   ├── regulatory_agent.py          # Country approval status
│   ├── qa_agent.py                  # Stability & re-evaluation
│   └── decision_synthesizer.py      # Final decision merger
├── tools/
│   ├── sql_executor.py              # Database query execution
│   ├── schema_fetcher.py            # Schema registry & aliases
│   └── audit_logger.py              # Decision audit logging
├── db/
│   ├── connection.py                # PostgreSQL connection manager
│   └── schema.sql                   # ai_decisions table schema
├── config.py                        # Configuration & environment variables
├── app.py                           # Flask API server
├── requirements.txt                 # Python dependencies
└── .env.example                     # Environment variables template
```

### Agent Flow

```
User Query / Scheduler
        ↓
   Router Agent (Intent Classification)
        ↓
   ┌────┴────┬────────┬────────┬────────┐
   ↓         ↓        ↓        ↓        ↓
Inventory  Demand  Logistics  Regulatory  QA
  Agent    Agent    Agent      Agent     Agent
   ↓         ↓        ↓        ↓        ↓
   └────┬────┴────────┴────────┴────────┘
        ↓
  Decision Synthesizer
        ↓
   Audit Logger → PostgreSQL
        ↓
   JSON Response
```

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- HuggingFace API token (for Llama 3.3 70B Instruct via HuggingFace Router)
- Access to clinical supply chain database with 40+ tables
- pip package manager

## Installation & Setup

### Step 1: Clone/Navigate to Project

```powershell
cd "Clinical Supply Chain Control Tower\backend"
```

### Step 2: Create Python Virtual Environment

```powershell
python -m venv venv
```

### Step 3: Activate Virtual Environment

```powershell
.\venv\Scripts\Activate
```

### Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

## Configuration

### Step 1: Create .env File

Copy the example file and configure:

```powershell
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` and configure the following:

```env
DB_NAME=clinical_supply_db
DB_USER=postgres
DB_PASS=your_secure_password
DB_HOST=localhost
DB_PORT=5432

LLM_API_KEY=your_huggingface_token_here
LLM_MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct:groq

EXPIRY_WARNING_DAYS=90
CRITICAL_EXPIRY=30
HIGH_EXPIRY=60
DEMAND_FORECAST_WEEKS=8
MAX_SQL_RETRY=3
```

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| DB_NAME | PostgreSQL database name | clinical_supply_db |
| DB_USER | Database username | postgres |
| DB_PASS | Database password | - |
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |
| LLM_API_KEY | HuggingFace API token | - |
| LLM_MODEL_NAME | LLM model identifier | meta-llama/Llama-3.3-70B-Instruct:groq |
| EXPIRY_WARNING_DAYS | Days before expiry to trigger warning | 90 |
| CRITICAL_EXPIRY | Days for critical expiry alert | 30 |
| HIGH_EXPIRY | Days for high priority expiry | 60 |
| DEMAND_FORECAST_WEEKS | Weeks to forecast demand | 8 |
| MAX_SQL_RETRY | Maximum SQL retry attempts | 3 |

## Database Setup

### Step 1: Ensure Read Access to Clinical Supply Tables

Verify you have SELECT permissions on these tables:

- Affiliate_Warehouse_Inventory
- Allocated_Materials
- Available_Inventory_Report
- Enrollment_Rate_Report
- Country_Level_Enrollment
- Distribution_Order_Report
- IP_Shipping_Timelines
- RIM
- Material_Country_Requirements
- Re_Evaluation
- QDocs
- Stability_Documents

### Step 2: Create ai_decisions Audit Table

Connect to your PostgreSQL database:

```powershell
psql -U postgres -d clinical_supply_db
```

Run the schema creation script:

```sql
\i db/schema.sql
```

Or manually execute:

```sql
CREATE TABLE IF NOT EXISTS ai_decisions (
    id SERIAL PRIMARY KEY,
    decision_json JSONB NOT NULL,
    decision_type VARCHAR(50),
    source_tables JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_decisions_timestamp ON ai_decisions(timestamp DESC);
CREATE INDEX idx_ai_decisions_type ON ai_decisions(decision_type);
```

### Step 3: Verify Table Creation

```sql
\dt ai_decisions
SELECT * FROM ai_decisions LIMIT 1;
```

## Running the Application

### Development Mode

```powershell
cd backend
python app.py
```

The server will start on `http://localhost:5000`

### Production Mode

For production deployment, use a WSGI server like Gunicorn:

```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing

### Test 1: Server Health Check

**Command:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Method GET
```

**Expected Response:**
```json
{
    "status": "ok"
}
```

### Test 2: Database Connection Test

**Command:**
```powershell
$body = @{
    query = "SELECT 1 AS test"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5000/api/sql" -Method POST -Body $body -ContentType "application/json"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
    "success": true,
    "data": [{"test": 1}],
    "row_count": 1
}
```

### Test 3: Query Available Inventory

**Command:**
```powershell
$body = @{
    query = "SELECT * FROM Available_Inventory_Report LIMIT 5"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5000/api/sql" -Method POST -Body $body -ContentType "application/json"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 4: Agent Routing - Inventory Check

**Command:**
```powershell
$body = @{
    query = "Check stock levels for Germany Trial ABC"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5000/api/query" -Method POST -Body $body -ContentType "application/json"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Response Structure:**
```json
{
    "decision": "YES",
    "severity": "HIGH",
    "risk_type": "EXPIRY",
    "weeks_of_cover": null,
    "reasoning": {
        "technical": "Analysis details...",
        "regulatory": "N/A",
        "logistical": "N/A"
    },
    "source_tables": ["Available_Inventory_Report", "Allocated_Materials"],
    "recommended_action": "Expedite usage or reallocate stock"
}
```

### Test 5: Agent Routing - Demand Forecast

**Command:**
```powershell
$body = @{
    query = "Predict demand for Trial ABC in Germany over next 8 weeks"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5000/api/query" -Method POST -Body $body -ContentType "application/json"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Test 6: Audit Log Validation

**SQL Query:**
```sql
SELECT 
    id,
    decision_type,
    decision_json->>'severity' as severity,
    source_tables,
    timestamp
FROM ai_decisions
ORDER BY timestamp DESC
LIMIT 5;
```

**Expected Results:**
- Decision JSON stored correctly
- Timestamp present
- Source tables array populated
- Decision type classified

### Test 7: Error Handling

**Test Invalid SQL:**
```powershell
$body = @{
    query = "DROP TABLE test"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:5000/api/sql" -Method POST -Body $body -ContentType "application/json"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
    "error": "Only SELECT queries are allowed"
}
```

## API Documentation

### GET /api/health

Health check endpoint.

**Response:**
```json
{
    "status": "ok"
}
```

### POST /api/query

Process natural language queries through the agent system.

**Request Body:**
```json
{
    "query": "Check inventory for Germany Trial ABC"
}
```

**Response:**
```json
{
    "decision": "YES|NO",
    "severity": "CRITICAL|HIGH|MEDIUM",
    "risk_type": "EXPIRY|SHORTFALL|LOGISTICS|REGULATORY|QA",
    "weeks_of_cover": number or null,
    "reasoning": {
        "technical": "string",
        "regulatory": "string",
        "logistical": "string"
    },
    "source_tables": ["table1", "table2"],
    "recommended_action": "string",
    "uncertainty": "optional string if data missing"
}
```

### POST /api/sql

Execute read-only SQL queries.

**Request Body:**
```json
{
    "query": "SELECT * FROM Available_Inventory_Report LIMIT 10"
}
```

**Response:**
```json
{
    "success": true,
    "data": [...],
    "row_count": 10
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Error message"
}
```

### GET /api/watchdog/run

Trigger for scheduled autonomous monitoring (placeholder).

**Response:**
```json
{
    "status": "not_implemented",
    "message": "Watchdog scheduler endpoint - to be implemented"
}
```

## Agent Details

### Router Agent
- **File:** `router_agent.py`
- **Purpose:** Intent classification and agent routing
- **LLM Usage:** Classifies user intent into STOCK, DEMAND, LOGISTICS, REGULATORY, QA, or GENERAL
- **Output:** Routes to appropriate domain agent

### Inventory Agent
- **File:** `inventory_agent.py`
- **Tables:** Affiliate_Warehouse_Inventory, Allocated_Materials, Available_Inventory_Report
- **Purpose:** Detect expiry risk and stock availability
- **Severity Rules:**
  - CRITICAL: < 30 days to expiry
  - HIGH: < 60 days to expiry
  - MEDIUM: < 90 days to expiry

### Demand Agent
- **File:** `demand_agent.py`
- **Tables:** Enrollment_Rate_Report, Country_Level_Enrollment, Available_Inventory_Report
- **Purpose:** Forecast demand based on 28-day enrollment velocity
- **Logic:** Calculates weeks_of_cover = inventory / weekly_consumption
- **Severity Rules:**
  - CRITICAL: < 2 weeks of cover
  - HIGH: < 4 weeks of cover
  - MEDIUM: < 8 weeks of cover

### Logistics Agent
- **File:** `logistics_agent.py`
- **Tables:** Distribution_Order_Report, IP_Shipping_Timelines
- **Purpose:** Validate shipping timelines and lead times
- **Severity Rules:**
  - CRITICAL: > 30 days lead time
  - HIGH: > 21 days lead time
  - MEDIUM: > 14 days lead time

### Regulatory Agent
- **File:** `regulatory_agent.py`
- **Tables:** RIM, Material_Country_Requirements
- **Purpose:** Check country approval status
- **Severity Rules:**
  - CRITICAL: Status = "REJECTED"
  - HIGH: Status = "PENDING" (urgent)
  - MEDIUM: Status = "PENDING"

### QA Agent
- **File:** `qa_agent.py`
- **Tables:** Re_Evaluation, QDocs, Stability_Documents
- **Purpose:** Check stability and re-evaluation history
- **Decision:** YES if past re-evaluation successful

### Decision Synthesizer Agent
- **File:** `decision_synthesizer.py`
- **Purpose:** Merge multiple agent outputs into final decision
- **Logic:**
  - Takes highest severity across agents
  - Combines all source tables
  - Merges reasoning from all agents
  - Provides comprehensive action plan

## Troubleshooting

### Database Connection Issues

**Error:** `Database connection failed`

**Solutions:**
1. Verify PostgreSQL is running:
   ```powershell
   Get-Service -Name postgresql*
   ```

2. Check credentials in `.env` file

3. Test connection manually:
   ```powershell
   psql -U postgres -d clinical_supply_db -h localhost
   ```

### LLM API Errors

**Error:** `LLM processing failed`

**Solutions:**
1. Verify HuggingFace token in `.env`
2. Check API quota: https://huggingface.co/settings/tokens
3. Test API connectivity to https://router.huggingface.co/v1
4. Ensure model name is correct: meta-llama/Llama-3.3-70B-Instruct:groq

### Import Errors

**Error:** `ModuleNotFoundError`

**Solutions:**
1. Ensure virtual environment is activated:
   ```powershell
   .\venv\Scripts\Activate
   ```

2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### SQL Execution Failures

**Error:** `SQL execution failed`

**Solutions:**
1. Verify table exists in database
2. Check table name spelling (case-sensitive)
3. Ensure read permissions on tables

### JSON Parsing Errors

**Error:** `Failed to parse JSON response`

**Solutions:**
1. Check LLM response format
2. Verify prompt templates in agent files
3. Review LLM model version compatibility
