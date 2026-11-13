# backend/ai/warmup.py
"""Charge les modèles en ARRIÈRE-PLAN au démarrage. L'état est exposé via GET /status.

.env : PRELOAD_MODELS=True (défaut) / False
"""
import logging
import os
import threading

logger = logging.getLogger(__name__)

STATE = {"translator": "pending", "intent_classifier": "pending", "code_model": "pending"}


def status() -> dict:
    busy = any(v in ("pending", "loading") for v in STATE.values())
    return {"ready": not busy, "models": dict(STATE)}


def _step(name, fn):
    STATE[name] = "loading"
    try:
        fn()
        STATE[name] = "ready"
    except Exception as exc:  # ne jamais faire planter le serveur
        STATE[name] = "failed"
        logger.warning("Warmup of %s failed: %s", name, exc)


def _translator():
    from ai.translate import ENABLED, preload

    if ENABLED:
        preload(("fr",))


def _classifier():
    from ai.analyze import preload

    preload()


def _generator():
    from ai.model import get_generator

    get_generator()


def _run():
    for name, fn in (("translator", _translator), ("intent_classifier", _classifier), ("code_model", _generator)):
        _step(name, fn)
    logger.info("Warmup finished: %s", STATE)


def start_warmup():
    if os.getenv("PRELOAD_MODELS", "True").lower() != "true":
        for k in STATE:
            STATE[k] = "lazy"  # chargé à la première requête
        return
    threading.Thread(target=_run, name="model-warmup", daemon=True).start()
