# backend/ai/translate.py
"""
Détection de la langue + traduction vers l'anglais (français, arabe) AVANT
la génération de code et la classification d'intention.

- Modèles Marian (Helsinki-NLP/opus-mt-XX-en, ~300 Mo chacun), chargés à la demande.
- Si le texte est déjà en anglais, ou ressemble à du code : AUCUNE traduction.
- Si la traduction échoue (pas de réseau...), on garde le texte d'origine : rien ne plante.

.env facultatif :
  TRANSLATE_PROMPTS=True
  TRANSLATE_FR_MODEL=Helsinki-NLP/opus-mt-fr-en
  TRANSLATE_AR_MODEL=Helsinki-NLP/opus-mt-ar-en
"""
import os
import re
import logging
import threading
from functools import lru_cache

logger = logging.getLogger(__name__)

ENABLED = os.getenv("TRANSLATE_PROMPTS", "True").lower() == "true"

MODELS = {
    "fr": os.getenv("TRANSLATE_FR_MODEL", "Helsinki-NLP/opus-mt-fr-en"),
    "ar": os.getenv("TRANSLATE_AR_MODEL", "Helsinki-NLP/opus-mt-ar-en"),
}

_pipes = {}
_lock = threading.Lock()

# Mots très fréquents : "a", "on", "code", "comment", "plus" sont volontairement absents (ambigus)
FR_WORDS = {
    "je", "veux", "voudrais", "un", "une", "le", "la", "les", "des", "du", "de", "pour", "avec",
    "qui", "que", "est", "et", "en", "dans", "sur", "au", "aux", "ce", "cette", "mon", "ma", "mes",
    "fonction", "écris", "ecris", "écrire", "crée", "cree", "créer", "creer", "ajoute", "donne",
    "moi", "programme", "calcule", "calculer", "calculatrice", "factorielle", "chaîne", "chaine",
    "liste", "nombre", "nombres", "trouver", "trouve", "inverse", "inverser", "affiche", "retourne",
    "vérifie", "verifie", "vérifier", "entier", "entiers", "tableau", "peux", "tu", "il", "si",
    "ou", "où", "pas", "trier", "tri", "somme", "maximum", "minimum", "caractères", "caracteres",
    "l", "d", "j", "qu", "svp", "s'il", "plait", "plaît", "texte", "fichier", "boucle", "récursive",
}
EN_WORDS = {
    "the", "an", "of", "to", "in", "for", "with", "that", "is", "and", "write", "create", "function",
    "make", "find", "return", "reverse", "string", "list", "number", "numbers", "calculate", "check",
    "print", "program", "how", "can", "you", "me", "want", "from", "all", "given", "by", "please",
    "calculator", "sort", "sum", "maximum", "minimum", "array", "loop", "file", "text", "implement",
}

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
ACCENT_RE = re.compile(r"[éèêëàâùûçôîïœ]", re.I)
WORD_RE = re.compile(r"[a-zà-ÿœ]+")

# Ligne qui ressemble à du code (début de ligne) -> on ne traduit jamais du code
CODE_LINE_RE = re.compile(
    r"^\s*(def |class |import |from \S+ import |public |private |protected |static |"
    r"for\s*\(|while\s*\(|if\s*\(|return\b|#include|package |@\w+|"
    r"(if|for|while|elif|else|try|except|with)\b.*:\s*$)",
    re.M,
)
BACKTICK_RE = re.compile(r"`([^`]+)`")


def looks_like_code(text: str) -> bool:
    return bool(CODE_LINE_RE.search(text)) or (text.count("{") + text.count(";")) >= 2


def detect_language(text: str) -> str:
    """'ar', 'fr' ou 'en' (par défaut). Heuristique rapide, sans modèle."""
    if ARABIC_RE.search(text):
        return "ar"
    words = WORD_RE.findall(text.lower())
    fr = sum(w in FR_WORDS for w in words)
    en = sum(w in EN_WORDS for w in words)
    if ACCENT_RE.search(text):
        fr += 2
    return "fr" if fr > en and fr >= 1 else "en"


def _get_pipe(lang: str):
    if lang not in _pipes:
        with _lock:
            if lang not in _pipes:
                from transformers import pipeline  # import tardif : module léger au démarrage
                logger.info("Loading translator %s ...", MODELS[lang])
                _pipes[lang] = pipeline("translation", model=MODELS[lang])
                logger.info("Translator loaded")
    return _pipes[lang]


def preload(langs=("fr",)):
    for lang in langs:
        _get_pipe(lang)


def _mask(text: str):
    """Protège les `noms_de_code` entre accents graves pour qu'ils ne soient pas traduits."""
    spans = []

    def repl(match):
        spans.append(match.group(1))
        return f"CODEX{len(spans) - 1}X"

    return BACKTICK_RE.sub(repl, text), spans


@lru_cache(maxsize=256)
def to_english(text: str):
    """Renvoie (texte_en_anglais, langue_détectée). langue = 'en', 'fr', 'ar' ou 'code'."""
    clean = " ".join((text or "").split())
    if not ENABLED or not clean:
        return clean, "en"
    if looks_like_code(text):
        return text, "code"

    lang = detect_language(clean)
    if lang == "en":
        return clean, "en"

    masked, spans = _mask(clean)
    try:
        out = _get_pipe(lang)(masked, max_length=256)[0]["translation_text"].strip()
    except Exception as exc:  # réseau, mémoire... : on garde l'original
        logger.warning("Translation unavailable (%s->en): %s", lang, exc)
        return clean, lang

    for i, original in enumerate(spans):
        token = f"CODEX{i}X"
        if token not in out:      # le traducteur a abîmé un nom de code : on garde l'original
            return clean, lang
        out = out.replace(token, original)
    return out, lang