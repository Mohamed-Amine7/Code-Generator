# backend/database.py
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
logger = logging.getLogger(__name__)


def _build_url():
    # DATABASE_URL (ex: sqlite:///./test.db pour les tests) prime sur DB_*
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "codehistory"),
        query={"charset": "utf8mb4"},
    )


DATABASE_URL = _build_url()
DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"

_kwargs = {"echo": DB_ECHO, "pool_pre_ping": True}
if str(DATABASE_URL).startswith("sqlite"):
    _kwargs["connect_args"] = {"check_same_thread": False}
else:
    _kwargs.update(pool_size=5, max_overflow=10, pool_recycle=1800, connect_args={"connect_timeout": 10})

engine = create_engine(DATABASE_URL, **_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as exc:
        logger.error("Database connection failed: %s", exc)
        return False
