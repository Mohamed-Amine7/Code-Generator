from ai.textutils import cut_java, cut_python, make_valid_python, normalize_language


def test_normalize_language():
    assert normalize_language("Java") == "java"
    assert normalize_language("javascript") == "python"
    assert normalize_language(None) == "python"


def test_cut_python_stops_at_unindented_line():
    text = "def f(x):\n    return x\n\nprint(f(1))\n"
    assert cut_python(text) == "def f(x):\n    return x"


def test_cut_python_allowed_starts():
    text = "def test_a():\n    assert 1\nimport os\nprint('x')"
    assert cut_python(text, allowed_starts=("import",)).endswith("import os")


def test_make_valid_python_drops_broken_tail():
    code = "def f(x):\n    return x\n\ndef g(:\n    pass"
    assert make_valid_python(code) == "def f(x):\n    return x"


def test_make_valid_python_impossible():
    assert make_valid_python("def (") is None


def test_cut_java_balanced():
    src = "public class A { void f() { } } trailing"
    assert cut_java(src) == "public class A { void f() { } }"


def test_cut_java_adds_missing_braces():
    assert cut_java("public class A { void f() {").endswith("}\n}")
