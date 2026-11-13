"""Configuration centralisée (lue depuis .env / variables d'environnement)."""
import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# --- Sécurité : aucune valeur par défaut pour la clé secrète -> l'app refuse de démarrer sans elle
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY manquante ou trop courte (32 caractères minimum). "
        "Génère-en une : python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
ALGORITHM = "HS256"  # fixé en dur : ne pas laisser l'algorithme dépendre d'une variable
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# --- Cookie d'authentification (httpOnly)
COOKIE_NAME = "access_token"
COOKIE_SECURE = _bool("COOKIE_SECURE", False)          # True en HTTPS
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # "none" si front et API sont sur des domaines différents (+ COOKIE_SECURE=True)

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# --- Base de données / migrations
AUTO_CREATE_TABLES = _bool("AUTO_CREATE_TABLES", True)  # mettre False en production et utiliser Alembic

# --- Limitation de débit (slowapi)
RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", True)
RATE_AUTH = os.getenv("RATE_AUTH", "10/minute")
RATE_HEAVY = os.getenv("RATE_HEAVY", "20/minute")  # routes qui appellent un modèle

# --- IA
GEN_QUEUE_TIMEOUT = float(os.getenv("GEN_QUEUE_TIMEOUT", "120"))  # attente max pour le verrou de génération (s)
