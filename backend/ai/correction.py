# backend/ai/correction.py
"""Correction : outils déterministes (ruff --fix, black) d'abord ; le modèle de code seulement
pour réparer une erreur de syntaxe restante. Renvoie aussi un diff."""
import ast
import difflib
import logging
import subprocess
import sys
from typing import Dict, Optional

from ai.validation import validate_code

logger = logging.getLogger(__name__)


def _ruff_fix(code: str) -> Optional[str]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "--exit-zero", "--preview", "--select", "E,F,W,I",
             "--ignore", "E501", "--stdin-filename", "code.py", "-"],
            input=code, capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = proc.stdout
    try:
        ast.parse(out)
    except SyntaxError:
        return None
    return out if out.strip() else None


def _black(code: str) -> Optional[str]:
    try:
        import black

        return black.format_str(code, mode=black.Mode(line_length=100))
    except Exception:
        return None


def repair_with_llm(code: str, error: str) -> Optional[str]:
    """Répare avec le modèle de code. Renvoie None si le résultat n'est pas du Python valide."""
    from ai.model import get_generator
    from ai.textutils import make_valid_python
    from ai.utils import complete

    prompt = (
        f"# Buggy Python code\n{code.strip()}\n\n"
        f"# Problem: {' '.join(error.split())[:300]}\n\n"
        "# Fixed version of the code above (same function names)\n"
    )
    stop = lambda new: "\n#" in new or "```" in new or "\n\n\n\n" in new
    new = complete(get_generator(), prompt, stop, 300).split("\n#")[0].split("```")[0]
    fixed = make_valid_python(new.strip())
    if not fixed or len(fixed) < 10 or fixed.strip() == code.strip():
        return None
    return fixed


def _diff(a: str, b: str) -> str:
    return "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), "original", "corrected"))


def correct_code(code: str, language: str = "python", use_llm: bool = True) -> Dict:
    if str(language).lower().startswith("java"):
        return {"original_code": code, "corrected_code": code, "diff": "", "changed": False, "language": "java",
                "fixes": ["Pas de correcteur automatique pour Java (utilise google-java-format ou ton IDE)."], "tools": []}

    before = validate_code(code, "python")
    current, fixes, tools = code, [], []

    fixed = _ruff_fix(current)
    if fixed is not None and fixed != current:
        current = fixed
        fixes.append("Corrections automatiques (ruff) : imports inutilisés, espaces, lignes vides…")
        tools.append("ruff")

    formatted = _black(current)
    if formatted is not None and formatted != current:
        current = formatted
        fixes.append("Mise en forme (black)")
        tools.append("black")

    after = validate_code(current, "python")
    if not after["valid"] and use_llm:
        err = next((a["message"] for a in after["annotations"] if a["type"] == "error"), "syntax error")
        try:
            repaired = repair_with_llm(current, err)
        except Exception as exc:  # modèle indisponible, occupé…
            logger.warning("LLM repair skipped: %s", exc)
            repaired = None
        if repaired:
            current = repaired
            fixes.append("Réparation de l'erreur de syntaxe par le modèle de code (à relire !)")
            tools.append("llm")
            after = validate_code(current, "python")

    if before["total_issues"] != after["total_issues"]:
        fixes.append(f"Problèmes détectés : {before['total_issues']} → {after['total_issues']}")
    if not fixes:
        fixes.append("Rien à corriger automatiquement")

    return {"original_code": code, "corrected_code": current, "diff": _diff(code, current),
            "changed": current != code, "language": "python", "fixes": fixes, "tools": tools}
