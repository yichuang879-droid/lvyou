"""
统一配置管理 —— 加载 .env + SQLAlchemy 引擎 + 所有环境变量。

使用方式:
  from app.config import SessionLocal, engine, LLM_API_KEY, AMAP_API_KEY
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ── 项目根目录 ──────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent  # backend/
load_dotenv(BACKEND_DIR / ".env")

# ── 数据库 (SQLite) ─────────────────────────────────────
DB_DIR = BACKEND_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = DB_DIR / "app.db"
DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── 大模型 (LLM) ───────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai_compatible")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL_ID", "qwen-plus")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "1"))

# ── 高德地图 ────────────────────────────────────────────
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
AMAP_BASE_URL = os.getenv("AMAP_BASE_URL", "https://restapi.amap.com/v3")
AMAP_DEFAULT_CITY = os.getenv("AMAP_DEFAULT_CITY", "")
AMAP_TIMEOUT_SECONDS = int(os.getenv("AMAP_TIMEOUT_SECONDS", "20"))
ENABLE_AMAP_ENRICHMENT = os.getenv("ENABLE_AMAP_ENRICHMENT", "false").lower() == "true"

# ── RAG / 向量库（预留） ─────────────────────────────────
CHROMA_DB_DIR = BACKEND_DIR / os.getenv("CHROMA_DB_DIR", "db/chroma_db")
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "travel_guides")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))
RERANK_MODEL = os.getenv("RERANK_MODEL", "qwen3-rerank")

# ── Redis 缓存（可选） ──────────────────────────────────
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "trip_planner")
REDIS_DEFAULT_TTL_SECONDS = int(os.getenv("REDIS_DEFAULT_TTL_SECONDS", "1800"))
REDIS_WEATHER_TTL_SECONDS = int(os.getenv("REDIS_WEATHER_TTL_SECONDS", "1800"))
REDIS_MAP_TTL_SECONDS = int(os.getenv("REDIS_MAP_TTL_SECONDS", "86400"))
REDIS_RAG_TTL_SECONDS = int(os.getenv("REDIS_RAG_TTL_SECONDS", "21600"))
REDIS_RERANK_TTL_SECONDS = int(os.getenv("REDIS_RERANK_TTL_SECONDS", "21600"))
