# backend/ai/explain.py
import ast

from ai.model import get_generator
from ai.utils import complete

WHO = {
    "beginner": "a complete beginner, in very simple words",
    "intermediate": "a developer with some experience, with technical details",
    "expert": "an expert, precisely, including complexity and edge cases",
}


def _fallback(code: str) -> str:
    """Résumé fiable construit avec l'analyse syntaxique (Python), sans IA."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "This code has a syntax error, so it cannot be explained reliably."
    parts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = ", ".join(a.arg for a in node.args.args) or "no arguments"
            line = f"Function `{node.name}` takes {args}."
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)
                     and getattr(n.func, "id", None) == node.name]
            if calls:
                line += " It calls itself (recursion)."
            if any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node)):
                line += " It uses a loop."
            if any(isinstance(n, ast.If) for n in ast.walk(node)):
                line += " It makes decisions with if/else."
            if any(isinstance(n, ast.Return) for n in ast.walk(node)):
                line += " It returns a result."
            parts.append(line)
    return "\n".join(parts) or "No function found in this code."


def explain_code(code: str, level: str = "beginner"):
    who = WHO.get((level or "beginner").lower(), WHO["beginner"])
    prompt = f"{code.strip()}\n\n---\nExplanation of the code above for {who}:\n\n1."
    stop = lambda t: "\n---" in t or "```" in t or "\n\n\n" in t

    text = "1." + complete(get_generator(), prompt, stop, 200)
    text = text.split("\n---")[0].split("```")[0].strip()

    # sortie vide ou qui recopie simplement le code -> résumé fiable
    if len(text) < 25 or text in code:
        return _fallback(code)
    return text