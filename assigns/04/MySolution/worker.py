"""One bounded language request, launched by the backend as a subprocess."""
import json
import sys
import lambda1 as lang
from reader import InputError, read_source


def contains_error(value):
    if type(value) is lang.D0V000:
        return True
    return (isinstance(value, lang.D0Vpair)
            and (contains_error(value.arg1) or contains_error(value.arg2)))


def perform(operation, source):
    try:
        expression = read_source(source)
    except InputError as exc:
        return {"outcome": "input_error", "text": str(exc)}
    try:
        if operation == "lint":
            names = lang.d0exp_fvset(expression)
            return {"outcome": "language_error" if names else "success",
                    "text": "Undeclared variables: " + ", ".join(sorted(names))
                    if names else "No free variables were found.",
                    "free_variables": sorted(names)}
        if operation != "interpret":
            raise ValueError("Unsupported worker operation.")
        value = lang.d0exp_evaluate(expression, lang.ENVnil())
        if contains_error(value):
            return {"outcome": "runtime_error",
                    "text": "Evaluation returned D0V000(): an unbound variable or invalid value (possibly inside a pair)."}
        output = repr(value)
        if len(output) > 16384:
            output = output[:16384] + "\n[Output truncated at 16,384 characters.]"
        return {"outcome": "success", "text": output}
    except (TypeError, ValueError, ArithmeticError, RecursionError) as exc:
        return {"outcome": "runtime_error", "text": f"{type(exc).__name__}: {exc}"[:16384]}
    except Exception as exc:
        return {"outcome": "backend_error", "text": f"Language backend failed: {type(exc).__name__}: {exc}"[:16384]}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    json.dump(perform(request["operation"], request["source"]), sys.stdout)
