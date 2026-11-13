from ai.validation import validate_code


def test_syntax_error_is_invalid_and_low_score():
    r = validate_code("def f(:\n    pass")
    assert r["valid"] is False
    assert r["quality_score"] <= 2.0
    assert r["annotations"][0]["type"] == "error"


def test_clean_code_scores_high():
    r = validate_code('def add(a, b):\n    """Add."""\n    return a + b\n')
    assert r["valid"] is True
    assert r["quality_score"] >= 9


def test_keyword_argument_is_not_flagged_as_spacing_issue():
    r = validate_code('def f(x):\n    """d"""\n    return x\n\n\nresult = f(x=1)\n')
    assert not any("espaces autour" in a["message"] for a in r["annotations"])


def test_mutable_default_and_bare_except_detected():
    code = 'def f(a=[]):\n    """d"""\n    try:\n        return a\n    except:\n        return None\n'
    msgs = " ".join(a["message"] for a in validate_code(code)["annotations"])
    assert "mutable" in msgs and "except" in msgs


def test_java_unbalanced_braces():
    assert validate_code("public class A { void f() {", "java")["valid"] is False
