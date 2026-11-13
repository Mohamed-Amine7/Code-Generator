# backend/ai/analyze.py
"""Classification d'intention : règles simples d'abord, zero-shot (NLI) en secours."""
import logging
import os
import re
import threading

logger = logging.getLogger(__name__)

INTENT_MODEL = os.getenv("INTENT_MODEL", "typeform/distilbert-base-uncased-mnli")
# Modèle plus précis (plus lourd) : INTENT_MODEL=MoritzLaurer/deberta-v3-base-zeroshot-v2.0
HYPOTHESIS = "The user wants to {}."

# label affiché -> formulation naturelle pour l'hypothèse NLI
LABELS = {
    "explain code": "understand or have some code explained",
    "generate tests": "get unit tests written",
    "give feedback": "get a review of some code",
    "general question": "ask a general question",
}

RULES = [
    ("generate tests", re.compile(r"\b(unit ?tests?|test cases?|pytest|junit|write (some )?tests?)\b", re.I)),
    ("give feedback", re.compile(r"\b(review|feedback|refactor|optimi[sz]e|improve|what'?s wrong|any bugs?)\b", re.I)),
    ("explain code", re.compile(r"\b(explain|what does|how does|walk me through|understand)\b", re.I)),
]

_classifier = None
_lock = threading.Lock()


def _get_classifier():
    global _classifier
    if _classifier is None:
        with _lock:
            if _classifier is None:
                from transformers import pipeline

                logger.info("Loading intent classifier %s ...", INTENT_MODEL)
                _classifier = pipeline("zero-shot-classification", model=INTENT_MODEL)
                logger.info("Intent classifier loaded")
    return _classifier


def preload():
    _get_classifier()


def analyze_text(text: str):
    text = (text or "").strip()
    if not text:
        return {"intent": "unknown", "score": 0.0, "confidence": 0.0, "scores": {}, "method": "none"}

    for label, pattern in RULES:
        if pattern.search(text):
            scores = {l: 0.0 for l in LABELS}
            scores[label] = 0.9
            return {"intent": label, "score": 0.9, "confidence": 0.9, "scores": scores, "method": "rules"}

    result = _get_classifier()(text, list(LABELS.values()), hypothesis_template=HYPOTHESIS)
    reverse = {v: k for k, v in LABELS.items()}
    scores = {reverse[l]: float(s) for l, s in zip(result["labels"], result["scores"])}
    best_label = reverse[result["labels"][0]]
    best = float(result["scores"][0])
    return {"intent": best_label, "score": best, "confidence": best, "scores": scores, "method": "model"}
