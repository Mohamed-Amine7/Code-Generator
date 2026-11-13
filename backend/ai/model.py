# backend/ai/model.py
"""
Chargement PARESSEUX du modèle de génération de code (une seule fois, thread-safe).

Variables .env facultatives :
  CODE_MODEL_NAME = deepseek-ai/deepseek-coder-1.3b-base   (défaut)
  USE_OFFLOAD     = False   (True seulement si la RAM est insuffisante)
  QUANTIZE        = False   (True : quantification int8 dynamique sur CPU -> ~2x plus rapide, ~4x moins de RAM sur les couches Linear)
  USE_GPU         = False   (True : charge le modèle en float16 sur CUDA si disponible)
"""
import logging
import os
import threading

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("CODE_MODEL_NAME", "deepseek-ai/deepseek-coder-1.3b-base")
USE_OFFLOAD = os.getenv("USE_OFFLOAD", "False").lower() == "true"
QUANTIZE = os.getenv("QUANTIZE", "True").lower() == "true"
USE_GPU = os.getenv("USE_GPU", "False").lower() == "true" and torch.cuda.is_available()
OFFLOAD_DIR = "./model_offload"

# Optimisation des threads CPU pour l'inférence locale
if not USE_GPU:
    _cpu_threads = int(os.getenv("TORCH_NUM_THREADS", str(min(4, os.cpu_count() or 1))))
    try:
        torch.set_num_threads(_cpu_threads)
        logger.info("PyTorch CPU threads set to %d", _cpu_threads)
    except Exception as _e:
        logger.debug("Could not set torch threads: %s", _e)

_lock = threading.Lock()
_cache = {}


def _load():
    if "code_generator" in _cache:
        return

    logger.info("Loading model %s (offload=%s, quantize=%s, gpu=%s) ...", MODEL_NAME, USE_OFFLOAD, QUANTIZE, USE_GPU)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    kwargs = dict(torch_dtype=torch.float16 if USE_GPU else torch.float32, low_cpu_mem_usage=True)
    if USE_OFFLOAD:
        os.makedirs(OFFLOAD_DIR, exist_ok=True)
        kwargs.update(device_map="auto", offload_folder=OFFLOAD_DIR)

    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, **kwargs)
    model.eval()

    if QUANTIZE and not USE_GPU and not USE_OFFLOAD:
        model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
        logger.info("Dynamic int8 quantization applied")
    if USE_GPU and not USE_OFFLOAD:
        model.to("cuda")

    _cache["tokenizer"] = tokenizer
    _cache["model"] = model
    _cache["code_generator"] = pipeline(
        "text-generation", model=model, tokenizer=tokenizer,
        device=0 if (USE_GPU and not USE_OFFLOAD) else None,
    )
    logger.info("Model loaded")


def get_generator():
    """Renvoie le pipeline, en le chargeant au premier appel."""
    if "code_generator" not in _cache:
        with _lock:
            _load()
    return _cache["code_generator"]


def __getattr__(name):
    if name in ("code_generator", "model", "tokenizer"):
        get_generator()
        return _cache[name]
    raise AttributeError(f"module 'ai.model' has no attribute {name!r}")
