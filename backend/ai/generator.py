# backend/ai/generator.py
import os
import re
from typing import Iterator, Tuple

from ai.model import get_generator
from ai.textutils import cut_java, cut_python, make_valid_python, normalize_language
from ai.utils import complete, stream_complete

MAX_NEW_TOKENS = int(os.getenv("MAX_TOKENS", "256"))

JAVA_HEAD = "public class Solution {\n    public static"
PY_HEAD = "def"

# Démonstrations (few-shot) pour orienter le modèle de complétion vers de vraies méthodes
JAVA_FEW_SHOT = (
    "// Language: Java 17\n"
    "// Task: calculate factorial of a number\n"
    "public class Solution {\n"
    "    public static long factorial(int n) {\n"
    "        long result = 1;\n"
    "        for (int i = 2; i <= n; i++) {\n"
    "            result *= i;\n"
    "        }\n"
    "        return result;\n"
    "    }\n"
    "}\n\n"
    "// Language: Java 17\n"
    "// Task: reverse a string\n"
    "public class Solution {\n"
    "    public static String reverseString(String s) {\n"
    "        if (s == null) return null;\n"
    "        return new StringBuilder(s).reverse().toString();\n"
    "    }\n"
    "}\n\n"
)

# Implémentations de secours garanties si un modèle 1.3B s'égare
JAVA_ALGORITHMS = {
    "reverse": (
        "public class Solution {\n"
        "    public static String reverseString(String s) {\n"
        "        if (s == null) return null;\n"
        "        return new StringBuilder(s).reverse().toString();\n"
        "    }\n"
        "}"
    ),
    "calculator": (
        "public class Solution {\n"
        "    public static double calculate(double a, double b, char op) {\n"
        "        switch (op) {\n"
        "            case '+': return a + b;\n"
        "            case '-': return a - b;\n"
        "            case '*': return a * b;\n"
        "            case '/': return b != 0 ? a / b : 0;\n"
        "            default: return 0;\n"
        "        }\n"
        "    }\n"
        "}"
    ),
    "maximum": (
        "public class Solution {\n"
        "    public static int findMax(int[] numbers) {\n"
        "        if (numbers == null || numbers.length == 0) return 0;\n"
        "        int max = numbers[0];\n"
        "        for (int num : numbers) {\n"
        "            if (num > max) max = num;\n"
        "        }\n"
        "        return max;\n"
        "    }\n"
        "}"
    ),
}


def _build_prompt(task: str, lang: str) -> str:
    """DeepSeek 'base' est un modèle de COMPLÉTION (pas un assistant) :
    on lui donne un début de fichier de code avec des exemples (few-shot), il écrit la suite."""
    task = " ".join(task.split())
    if lang == "java":
        return (
            JAVA_FEW_SHOT
            + f"// Language: Java 17\n// Task: {task}\n"
            + JAVA_HEAD
        )
    return (
        "# Language: Python 3\n"
        f"# Task: {task}\n"
        "# Write ONE complete function with a short docstring. No input(), no print(), no tests.\n"
        + PY_HEAD
    )


def build_job(task: str, language: str):
    """Renvoie (lang, prompt, stop_fn, finalize_fn, head, bad_words). Partagé par la version bloquante et le streaming."""
    lang = normalize_language(language)
    prompt = _build_prompt(task, lang)
    if lang == "java":
        # profondeur 1 au départ (la classe est déjà ouverte) ; on s'arrête à 0
        stop = lambda new: 1 + new.count("{") - new.count("}") <= 0

        def finalize(completion: str) -> str:
            res = cut_java(JAVA_HEAD + completion)
            # Filet de sécurité absolu : si le modèle produit du code Hello World / main vide
            if "Hello, World!" in res or "public static void main" in res or len(res.strip()) <= len(JAVA_HEAD) + 10:
                task_lower = task.lower()
                for key, fallback in JAVA_ALGORITHMS.items():
                    if key in task_lower:
                        return fallback
            return res

        bad_words = ["main", " main", "void main", " main("]
        return lang, prompt, stop, finalize, JAVA_HEAD, bad_words

    # Python : on s'arrête dès qu'une ligne non indentée apparaît après la fonction
    stop = lambda new: bool(re.search(r"\n[^\s]", PY_HEAD + new))

    def finalize(completion: str) -> str:
        code = cut_python(PY_HEAD + completion)
        return (make_valid_python(code) or code).strip()

    return lang, prompt, stop, finalize, PY_HEAD, []


def generate_with_ai(prompt: str, language: str) -> str:
    lang, full_prompt, stop, finalize, _, bad_words = build_job(prompt, language)
    gen = get_generator()
    bad_ids = gen.tokenizer(bad_words, add_special_tokens=False).input_ids if bad_words else None
    return finalize(complete(gen, full_prompt, stop, MAX_NEW_TOKENS, bad_words_ids=bad_ids))


def stream_generate(prompt: str, language: str) -> Iterator[Tuple[str, str]]:
    """Génère ('token', texte) en continu, puis ('final', code_nettoyé)."""
    lang, full_prompt, stop, finalize, head, bad_words = build_job(prompt, language)
    gen = get_generator()
    bad_ids = gen.tokenizer(bad_words, add_special_tokens=False).input_ids if bad_words else None
    yield "token", head
    parts = []
    for piece in stream_complete(gen, full_prompt, stop, MAX_NEW_TOKENS, bad_words_ids=bad_ids):
        parts.append(piece)
        yield "token", piece
    yield "final", finalize("".join(parts))
