import os
from dotenv import load_dotenv

load_dotenv()

def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

DB_PATH = env("MEMORYOS_DB", "memoryos.db")
HINDSIGHT_BASE_URL = env("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_API_KEY = env("HINDSIGHT_API_KEY")
HINDSIGHT_BANK_ID = env("HINDSIGHT_BANK_ID", "memoryos-company-brain")
GROQ_API_KEY = env("GROQ_API_KEY")
GROQ_MODEL = env("GROQ_MODEL", "llama-3.3-70b-versatile")
JWT_SECRET = env("JWT_SECRET", "change-me-in-production")
DECAY_HALF_LIFE_DAYS = float(env("MEMORY_HALF_LIFE_DAYS", "60"))
CORS_ORIGINS = env("CORS_ORIGINS", "http://localhost:3000").split(",")