# Clinical Supply Chain Control Tower

A multi-agent AI system for autonomous monitoring and risk analysis in clinical supply chains, addressing critical challenges like stock-outs during enrollment spikes and high-value drug batch expiration.

## Features

- **Multi-Agent Architecture**: Specialized agents for inventory, demand, logistics, regulatory compliance, and quality assurance
- **Intelligent Risk Detection**: Automated analysis of expiry risks, supply shortfalls, and shipping delays
- **Natural Language Interface**: Query the system using plain English
- **Real-time Analysis**: PostgreSQL integration for live data monitoring
- **Auditable Decisions**: Complete logging of all AI-driven decisions
- **RESTful API**: Easy integration with existing systems

## Architecture

```
backend/
├── agents/              # Specialized AI agents
│   ├── router_agent.py          # Intent classification & routing
│   ├── inventory_agent.py       # Stock & expiry detection
│   ├── demand_agent.py          # Demand forecasting
│   ├── logistics_agent.py       # Shipping validation
│   ├── regulatory_agent.py      # Compliance checking
│   └── qa_agent.py              # Quality assurance
├── tools/               # Utility modules
├── db/                  # Database management
├── config.py            # Configuration
└── app.py               # Flask API server

frontend/
└── app.py               # Streamlit web interface
```

## Tech Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **AI Model**: Llama 3.3 70B Instruct (via HuggingFace Router)
- **Frontend**: Streamlit

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- HuggingFace API token

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/divyanshu-prakash-rx/Clinical_Supply_Chain_Control_Tower.git
cd Clinical_Supply_Chain_Control_Tower
```

2. **Set up backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate
pip install -r requirements.txt
```

3. **Configure environment**

Create `backend/.env`:
```env
DB_NAME=clinical_supply_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

LLM_API_KEY=your_huggingface_token
LLM_MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct:groq
```

4. **Set up database**
```bash
psql -U postgres -d clinical_supply_db -f db/schema.sql
```

5. **Run backend**
```bash
python app.py
```

6. **Run frontend** (optional)
```bash
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

## API Usage

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Query Agent System
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Check stock levels for Trial ABC in Germany"}'
```

### Direct SQL Execution
```bash
curl -X POST http://localhost:5000/api/sql \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM Available_Inventory_Report LIMIT 5"}'
```

## Frontend Application

A Streamlit-based web interface is available in the `frontend/` directory.

### Frontend Setup

1. Navigate to frontend directory:
   ```powershell
   cd frontend
   ```

2. Create and activate virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the application:
   ```powershell
   streamlit run app.py
   ```

5. Access at: `http://localhost:8501`

## Agent System

| Agent | Purpose | Key Tables |
|-------|---------|------------|
| **Router** | Classifies user intent and routes to appropriate agent | - |
| **Inventory** | Detects expiry risks and stock availability | Available_Inventory_Report, Allocated_Materials |
| **Demand** | Forecasts demand based on enrollment velocity | Enrollment_Rate_Report, Country_Level_Enrollment |
| **Logistics** | Validates shipping timelines and lead times | Distribution_Order_Report, IP_Shipping_Timelines |
| **Regulatory** | Checks country approval status | RIM, Material_Country_Requirements |
| **QA** | Monitors stability and re-evaluation history | Re_Evaluation, Stability_Documents |

## Response Format

```json
{
  "decision": "YES|NO",
  "severity": "CRITICAL|HIGH|MEDIUM",
  "risk_type": "EXPIRY|SHORTFALL|LOGISTICS|REGULATORY|QA",
  "weeks_of_cover": 4.2,
  "reasoning": {
    "technical": "Detailed analysis...",
    "regulatory": "Compliance status...",
    "logistical": "Shipping considerations..."
  },
  "source_tables": ["table1", "table2"],
  "recommended_action": "Specific recommendations..."
}
```
## Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `EXPIRY_WARNING_DAYS` | Days before expiry to trigger warning | 90 |
| `CRITICAL_EXPIRY` | Days for critical expiry alert | 30 |
| `HIGH_EXPIRY` | Days for high priority expiry | 60 |
| `DEMAND_FORECAST_WEEKS` | Weeks to forecast demand | 8 |

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
- Each agent is independent and can be tested/modified separately
- Dynamic schema detection handles database variations
- All decisions are logged to `ai_decisions` table for audit trails

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This system requires access to a PostgreSQL database with clinical supply chain data. Ensure proper database permissions and API credentials before deployment.
