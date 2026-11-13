# backend/ai/testgen.py  (anciennement tests.py : renommé pour ne pas être pris pour un fichier de tests)
import re

from ai.model import get_generator
from ai.textutils import cut_java, cut_python, make_valid_python
from ai.utils import complete

JAVA_TEST_HEAD = (
    "import org.junit.jupiter.api.Test;\n"
    "import static org.junit.jupiter.api.Assertions.*;\n\n"
    "public class SolutionTest {\n    @Test\n    void"
)
PY_ALLOWED = ("def test", "@", "import", "from", "#")


def _is_java(code: str) -> bool:
    return "{" in code and ("public " in code or "class " in code)


def generate_tests(code: str):
    gen = get_generator()
    code = code.strip()

    if _is_java(code):
        prompt = f"// Code under test\n{code}\n\n// JUnit 5 tests for the code above\n{JAVA_TEST_HEAD}"
        stop = lambda new: 1 + new.count("{") - new.count("}") <= 0
        completion = complete(gen, prompt, stop, 300)
        return cut_java(JAVA_TEST_HEAD + completion)

    prompt = f"{code}\n\n\n# pytest unit tests for the function above (normal cases and edge cases)\ndef test"
    stop = lambda new: bool(re.search(r"\n(?!def test|@|import|from|#)[^\s]", "def test" + new))
    completion = complete(gen, prompt, stop, 300)
    tests = cut_python("def test" + completion, allowed_starts=PY_ALLOWED)
    tests = make_valid_python(tests) or tests
    return f"{code}\n\n\n{tests}"
