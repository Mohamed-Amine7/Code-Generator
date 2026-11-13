from ai.translate import detect_language, looks_like_code, to_english


def test_detect_language():
    assert detect_language("Écris une fonction qui calcule la factorielle") == "fr"
    assert detect_language("Write a function that reverses a string") == "en"
    assert detect_language("اكتب دالة") == "ar"


def test_looks_like_code():
    assert looks_like_code("def f(x):\n    return x")
    assert not looks_like_code("reverse a string")


def test_english_and_code_are_not_translated():
    assert to_english("Reverse a string in Python") == ("Reverse a string in Python", "en")
    assert to_english("def f(x):\n    return x")[1] == "code"
