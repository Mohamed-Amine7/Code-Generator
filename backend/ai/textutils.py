"""Fonctions pures (sans torch/transformers) : nettoyage du code généré. Faciles à tester."""
import ast


def normalize_language(language):
    lang = (language or "python").strip().lower()
    return "java" if lang.startswith("java") and "script" not in lang else "python"


def cut_python(text, allowed_starts=()):
    """Garde le premier bloc de code Python.
    Coupe dès qu'une ligne NON indentée apparaît (Test:, print(...), Expected output:, autre def...)
    sauf si elle commence par un des préfixes autorisés."""
    lines = text.split("\n")
    kept = lines[:1]
    for line in lines[1:]:
        if line and not line[0].isspace():
            if allowed_starts and line.startswith(tuple(allowed_starts)):
                kept.append(line)
                continue
            break
        kept.append(line)
    return "\n".join(kept).rstrip()


def make_valid_python(code, max_drop=25):
    """Si la génération a été coupée en plein milieu, retire les dernières lignes
    jusqu'à obtenir du Python syntaxiquement valide. Renvoie None si impossible."""
    code = code.rstrip()
    for _ in range(max_drop + 1):
        try:
            ast.parse(code)
            return code
        except SyntaxError:
            lines = code.split("\n")
            if len(lines) <= 1:
                break
            code = "\n".join(lines[:-1]).rstrip()
    return None


def cut_java(full_text):
    """Coupe à l'accolade fermante qui équilibre la première accolade ouvrante,
    et ajoute les accolades manquantes si la génération a été interrompue."""
    depth = 0
    started = False
    for i, ch in enumerate(full_text):
        if ch == "{":
            depth += 1
            started = True
        elif ch == "}":
            depth -= 1
            if started and depth <= 0:
                return full_text[: i + 1].strip()
    text = full_text.rstrip()
    if started and depth > 0:
        text += "\n" + "\n".join("}" for _ in range(depth))
    return text
