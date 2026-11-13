# backend/ai/verify.py
"""Générer -> tester -> réparer (une fois). Python uniquement, nécessite la sandbox Docker."""
import logging
from typing import Tuple

from ai.sandbox import run_python_tests, sandbox_available

logger = logging.getLogger(__name__)


def verify_and_repair(code: str, task: str, max_repairs: int = 1) -> Tuple[str, dict]:
    if not sandbox_available():
        return code, {"status": "skipped", "detail": "Sandbox disabled (set SANDBOX_MODE=docker)"}

    from ai.correction import repair_with_llm
    from ai.testgen import generate_tests

    current = code
    result = run_python_tests(generate_tests(current))
    attempts = 0
    while result.get("status") == "failed" and attempts < max_repairs:
        attempts += 1
        error = "; ".join(result.get("failures", []))[:400]
        repaired = repair_with_llm(current, f"tests failed for task '{task}': {error}")
        if not repaired:
            break
        second = run_python_tests(generate_tests(repaired))
        if second.get("status") == "passed":
            return repaired, {**second, "status": "repaired", "repairs": attempts}
        result = second
        break

    # NB : les tests sont écrits par le même petit modèle ; un échec peut venir du test lui-même.
    result["repairs"] = attempts
    return code, result
