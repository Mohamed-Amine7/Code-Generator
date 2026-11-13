from fastapi import APIRouter

from ai.warmup import status
from database import check_database_connection
from services.cache import get_cache_stats

router = APIRouter(tags=["status"])


@router.get("/")
def root():
    return {"status": "API is running"}


@router.get("/status")
def models_status():
    """Utilisé par le frontend pour afficher « modèles en cours de chargement »."""
    data = status()
    data["cache"] = get_cache_stats()
    return data


@router.get("/health")
def health_check():
    """Vérification de santé complète pour Docker, load balancers et monitoring."""
    db_ok = check_database_connection()
    model_st = status()
    is_healthy = db_ok and model_st.get("ready", False)
    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "models": model_st.get("models", {}),
        "models_ready": model_st.get("ready", False),
        "cache": get_cache_stats(),
    }
