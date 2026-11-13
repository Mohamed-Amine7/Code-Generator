from ai.generator import build_job


def test_build_job_python():
    lang, prompt, stop, finalize, head, bad_words = build_job("reverse a string", "python")
    assert lang == "python"
    assert "Language: Python 3" in prompt
    assert head == "def"
    sample_completion = " reverse_string(s):\n    return s[::-1]\n\nprint('hello')"
    cleaned = finalize(sample_completion)
    assert cleaned == "def reverse_string(s):\n    return s[::-1]"


def test_build_job_java_prompt_has_few_shot_and_bad_words():
    lang, prompt, stop, finalize, head, bad_words = build_job("reverse a string", "java")
    assert lang == "java"
    assert "factorial" in prompt  # Few-shot demonstration
    assert "No main method" not in prompt  # Negative priming bug removed
    assert head == "public class Solution {\n    public static"
    assert "main" in bad_words  # main is explicitly banned

    # 1. Normal clean Java completion
    sample_completion = " String reverse(String s) {\n        return new StringBuilder(s).reverse().toString();\n    }\n}"
    cleaned = finalize(sample_completion)
    assert "public static String reverse(String s)" in cleaned
    assert cleaned.endswith("}")

    # 2. Safety net: if model ever generates a dummy Hello World main, fallback catches it
    dummy_main = " void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"
    recovered = finalize(dummy_main)
    assert "Hello, World!" not in recovered
    assert "reverseString" in recovered
