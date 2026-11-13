# backend/ai/validation.py
"""Validation par analyse statique réelle (plus de score 'variance CodeBERT').

Python : ast (syntaxe) + pyflakes + règles ast + ruff (style) + bandit (sécurité), si installés.
Java   : javac -Xlint (si disponible), sinon vérification des accolades.
"""
import ast
import io
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_LINE = 120
PENALTY = {"high": 3.0, "medium": 1.0, "low": 0.3}


def _ann(line: int, type_: str, severity: str, message: str, source: str) -> Dict:
    return {"line": int(line or 0), "type": type_, "severity": severity, "message": message, "source": source}


def _run(cmd: List[str], stdin: Optional[str] = None, timeout: int = 20):
    try:
        return subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("Tool %s unavailable: %s", cmd[0], exc)
        return None


# ------------------------------------------------------------------ Python
def _pyflakes(tree) -> List[Dict]:
    try:
        from pyflakes.checker import Checker
    except ImportError:
        return []
    out = []
    for m in sorted(Checker(tree, "code.py").messages, key=lambda m: m.lineno):
        is_error = m.__class__.__name__ in ("UndefinedName", "UndefinedLocal")
        out.append(_ann(m.lineno, "error" if is_error else "warning", "high" if is_error else "medium",
                        m.message % m.message_args, "pyflakes"))
    return out


def _ast_checks(tree) -> List[Dict]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_") and not node.name.startswith("test_") and ast.get_docstring(node) is None:
                out.append(_ann(node.lineno, "suggestion", "low", f"`{node.name}` n'a pas de docstring", "ast"))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        out.append(_ann(d.lineno, "warning", "medium",
                                        "Valeur par défaut mutable (liste/dict/set) : elle est partagée entre les appels", "ast"))
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append(_ann(node.lineno, "warning", "medium", "`except:` nu : capture aussi KeyboardInterrupt/SystemExit", "ast"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            out.append(_ann(node.lineno, "warning", "high", f"Appel à `{node.func.id}` : exécution de code arbitraire", "ast"))
    return out


def _comment_checks(code: str) -> List[Dict]:
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.COMMENT and re.search(r"\b(TODO|FIXME)\b", tok.string, re.I):
                out.append(_ann(tok.start[0], "info", "low", "Code incomplet (TODO/FIXME)", "tokenize"))
    except (tokenize.TokenError, IndentationError):
        pass
    return out


def _line_length(code: str) -> List[Dict]:
    return [
        _ann(i, "warning", "low", f"Ligne trop longue ({len(l)} caractères, max recommandé : {MAX_LINE})", "length")
        for i, l in enumerate(code.splitlines(), 1) if len(l) > MAX_LINE
    ]


def _ruff_style(code: str) -> List[Dict]:
    proc = _run([sys.executable, "-m", "ruff", "check", "--preview", "--select", "E,W", "--ignore", "E501",
                 "--output-format", "json", "--stdin-filename", "code.py", "-"], stdin=code)
    if not proc or not proc.stdout.strip():
        return []
    try:
        items = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return [_ann(i["location"]["row"], "warning", "low", f"{i['message']} ({i['code']})", "ruff") for i in items]


def _bandit(code: str) -> List[Dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "code.py"
        path.write_text(code, encoding="utf-8")
        proc = _run([sys.executable, "-m", "bandit", "-q", "-f", "json", str(path)])
    if not proc or not proc.stdout.strip():
        return []
    try:
        results = json.loads(proc.stdout).get("results", [])
    except json.JSONDecodeError:
        return []
    return [_ann(r["line_number"], "warning", r["issue_severity"].lower(), f"Sécurité : {r['issue_text']}", "bandit")
            for r in results]


def _python_report(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [_ann(exc.lineno or 0, "error", "high", f"Erreur de syntaxe : {exc.msg}", "ast")], False, ["ast"]
    anns = _pyflakes(tree) + _ast_checks(tree) + _comment_checks(code) + _line_length(code) + _ruff_style(code) + _bandit(code)
    return anns, True, ["ast", "pyflakes", "ruff", "bandit"]


# ------------------------------------------------------------------ Java
def _java_report(code: str):
    if code.count("{") != code.count("}"):
        return [_ann(0, "error", "high", "Accolades non équilibrées", "braces")], False, ["braces"]
    if not shutil.which("javac"):
        return [_ann(0, "info", "low", "javac introuvable : seule la structure a été vérifiée", "braces")], True, ["braces"]
    match = re.search(r"public\s+(?:final\s+)?(?:class|interface|enum|record)\s+(\w+)", code)
    name = match.group(1) if match else "Solution"
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / f"{name}.java").write_text(code, encoding="utf-8")
        proc = _run(["javac", "-Xlint:all", "-d", tmp, str(Path(tmp) / f"{name}.java")], timeout=30)
    if proc is None:
        return [], True, ["braces"]
    anns, ok = [], True
    for m in re.finditer(r"\.java:(\d+):\s+(error|warning):\s+(.*)", proc.stderr):
        is_err = m.group(2) == "error"
        ok = ok and not is_err
        anns.append(_ann(int(m.group(1)), "error" if is_err else "warning", "high" if is_err else "medium", m.group(3), "javac"))
    return anns, ok, ["javac"]


# ------------------------------------------------------------------ API
def validate_code(code: str, language: str = "python") -> Dict:
    from services.cache import get_cached, set_cached

    lang = "java" if str(language).lower().startswith("java") and "script" not in str(language).lower() else "python"
    cache_key = f"{lang}:{code.strip()}"
    hit = get_cached("validation", cache_key)
    if hit is not None:
        return hit

    anns, syntax_ok, tools = _java_report(code) if lang == "java" else _python_report(code)
    anns.sort(key=lambda a: (a["line"], a["type"]))

    score = max(0.0, 10.0 - sum(PENALTY.get(a["severity"], 0.3) for a in anns))
    if not syntax_ok:
        score = min(score, 2.0)
    result = {
        "valid": syntax_ok,
        "quality_score": round(score, 1),
        "annotations": anns,
        "total_issues": len(anns),
        "language": lang,
        "tools": tools,
    }
    set_cached("validation", cache_key, result)
    return result
