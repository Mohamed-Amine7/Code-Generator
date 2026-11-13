# backend/ai/feedback.py
"""Revue de code : le modèle de code (DeepSeek) + les constats d'analyse statique."""
from ai.model import get_generator
from ai.utils import complete
from ai.validation import validate_code


def _static_summary(code: str, language: str) -> str:
    report = validate_code(code, language)
    notes = [f"- line {a['line']}: {a['message']}" if a["line"] else f"- {a['message']}" for a in report["annotations"][:10]]
    head = f"Static analysis score: {report['quality_score']}/10."
    return head + ("\n" + "\n".join(notes) if notes else " No issue found.")


def give_feedback(code: str, language: str = "python") -> str:
    code = code.strip()
    static = _static_summary(code, language)

    prompt = (
        f"{code}\n\n---\n"
        "Code review of the code above. Numbered list of concrete problems "
        "(bugs, edge cases, style, performance) and how to fix them:\n\n1."
    )
    stop = lambda t: "\n---" in t or "```" in t or "\n\n\n" in t
    text = "1." + complete(get_generator(), prompt, stop, 200)
    text = text.split("\n---")[0].split("```")[0].strip()

    if len(text) < 25 or text in code:
        return static
    return f"{text}\n\n[{static.splitlines()[0]}]" if static.startswith("Static") else text
