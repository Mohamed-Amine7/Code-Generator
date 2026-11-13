# backend/ai/utils.py
"""Outils de génération : arrêt personnalisé, complétion bloquante et en streaming."""
import threading
from typing import Iterator

import torch
from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer

from ai.textutils import (  # noqa: F401  (ré-exportés pour compatibilité)
    cut_java,
    cut_python,
    make_valid_python,
    normalize_language,
)
from core import config
from core.errors import GenerationBusy

# Une seule génération à la fois (CPU). Les autres attendent GEN_QUEUE_TIMEOUT secondes puis reçoivent un 503.
_GEN_LOCK = threading.Lock()


class StopWhen(StoppingCriteria):
    """Arrête la génération dès que should_stop(texte_nouveau) est vrai."""

    def __init__(self, tokenizer, should_stop):
        self.tokenizer = tokenizer
        self.should_stop = should_stop
        self.start = None

    def __call__(self, input_ids, scores, **kwargs):
        if self.start is None:
            self.start = input_ids.shape[1]
        new_text = self.tokenizer.decode(input_ids[0, self.start:], skip_special_tokens=True)
        done = bool(self.should_stop(new_text))
        return torch.tensor([done], dtype=torch.bool, device=input_ids.device)


def _acquire():
    if not _GEN_LOCK.acquire(timeout=config.GEN_QUEUE_TIMEOUT):
        raise GenerationBusy("The model is busy, please retry in a moment.")


def complete(gen, prompt, should_stop, max_new_tokens=256, bad_words_ids=None):
    """Complète `prompt` et renvoie UNIQUEMENT le texte nouveau."""
    _acquire()
    try:
        kwargs = dict(
            max_new_tokens=max_new_tokens,
            do_sample=False,
            return_full_text=False,
            pad_token_id=gen.tokenizer.eos_token_id,
            stopping_criteria=StoppingCriteriaList([StopWhen(gen.tokenizer, should_stop)]),
        )
        if bad_words_ids:
            kwargs["bad_words_ids"] = bad_words_ids
        out = gen(prompt, **kwargs)
    finally:
        _GEN_LOCK.release()
    return out[0]["generated_text"]


def stream_complete(gen, prompt, should_stop, max_new_tokens=256, bad_words_ids=None) -> Iterator[str]:
    """Même chose que complete(), mais renvoie le texte morceau par morceau."""
    _acquire()
    streamer = TextIteratorStreamer(gen.tokenizer, skip_prompt=True, skip_special_tokens=True)
    inputs = gen.tokenizer(prompt, return_tensors="pt")

    def run():
        try:
            kwargs = dict(
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=gen.tokenizer.eos_token_id,
                streamer=streamer,
                stopping_criteria=StoppingCriteriaList([StopWhen(gen.tokenizer, should_stop)]),
            )
            if bad_words_ids:
                kwargs["bad_words_ids"] = bad_words_ids
            gen.model.generate(
                **inputs,
                **kwargs,
            )
        except Exception:
            streamer.end()  # débloque le consommateur
            raise
        finally:
            _GEN_LOCK.release()

    threading.Thread(target=run, name="gen-stream", daemon=True).start()
    for piece in streamer:
        yield piece
