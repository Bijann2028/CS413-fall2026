"""Read constructor expressions using AST inspection, never eval or exec."""
import ast
import lambda1 as lang
from contracts import MAX_SOURCE_BYTES

SCHEMA = {
    "D0Eint": (int,), "D0Ebtf": (bool,), "D0Evar": (str,),
    "D0Eop1": (str, lang.D0E000),
    "D0Eop2": (str, lang.D0E000, lang.D0E000),
    "D0Elam": (str, lang.D0E000),
    "D0Efix": (str, str, lang.D0E000),
    "D0Eapp": (lang.D0E000, lang.D0E000),
    "D0Eif0": (lang.D0E000, lang.D0E000, lang.D0E000),
    "D0Elet": (str, lang.D0E000, lang.D0E000),
    "D0Epair": (lang.D0E000, lang.D0E000),
    "D0Epfst": (lang.D0E000,), "D0Epsnd": (lang.D0E000,),
}


class InputError(ValueError):
    pass


def read_source(source: str) -> lang.d0exp:
    if not source.strip():
        raise InputError("Source must not be empty.")
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise InputError("Source exceeds 65,536 UTF-8 bytes.")
    try:
        tree = ast.parse(source.strip(), mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise InputError(f"Invalid constructor expression: {exc}") from exc
    if sum(1 for _ in ast.walk(tree)) > 4096:
        raise InputError("Expression exceeds 4,096 AST nodes.")

    def build(node, depth=0):
        if depth > 100:
            raise InputError("Constructor nesting exceeds 100 levels.")
        if isinstance(node, ast.Constant) and type(node.value) in (int, bool, str):
            return node.value
        if (isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd))
                and isinstance(node.operand, ast.Constant)
                and type(node.operand.value) is int):
            return -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in SCHEMA):
            raise InputError("Only approved D0E constructors and literal arguments are allowed.")
        name = node.func.id
        schema = SCHEMA[name]
        if node.keywords or len(node.args) != len(schema):
            raise InputError(f"{name} requires {len(schema)} positional arguments.")
        values = [build(arg, depth + 1) for arg in node.args]
        for index, (value, expected) in enumerate(zip(values, schema), 1):
            valid = isinstance(value, expected) if expected is lang.D0E000 else type(value) is expected
            if not valid:
                raise InputError(f"{name} argument {index} must be {expected.__name__}.")
        return getattr(lang, name)(*values)

    result = build(tree.body)
    if not isinstance(result, lang.D0E000):
        raise InputError("The input must produce a d0exp, not a literal.")
    return result
