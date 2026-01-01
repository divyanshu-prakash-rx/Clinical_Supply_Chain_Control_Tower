import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'clinical_supply_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

LLM_API_KEY = os.getenv('LLM_API_KEY', '')  # HuggingFace token
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'meta-llama/Llama-3.3-70B-Instruct:groq')

# Initialize OpenAI client with HuggingFace router
from openai import OpenAI

LLM_CLIENT = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=LLM_API_KEY
) if LLM_API_KEY else None

EXPIRY_WARNING_DAYS = int(os.getenv('EXPIRY_WARNING_DAYS', '90'))
CRITICAL_EXPIRY = int(os.getenv('CRITICAL_EXPIRY', '30'))
HIGH_EXPIRY = int(os.getenv('HIGH_EXPIRY', '60'))
DEMAND_FORECAST_WEEKS = int(os.getenv('DEMAND_FORECAST_WEEKS', '8'))
MAX_SQL_RETRY = int(os.getenv('MAX_SQL_RETRY', '3'))
