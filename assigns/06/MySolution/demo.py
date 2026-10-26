"""Run with python -B -m MySolution.demo from assigns/06/."""

import argparse
import json
from pathlib import Path

from .compiler import compile_expr
from .evaluator import evaluate, source_data
from .examples import required_examples
from .observe import observe
from .source_ops import format_source
from .terms import format_term


def run_example(example, output):
    term = compile_expr(example.expression)
    term_path = output / f"{example.name}.lambda.txt"
    term_path.write_text(format_term(term) + "\n", encoding="utf-8")
    execution = evaluate(term, example.execution_budget)
    record = {
        "name": example.name,
        "source": format_source(example.expression),
        "target_file": str(term_path),
        "expected_kind": example.kind,
        "expected": "budget exhaustion" if example.exhausts else example.expected,
        "execution_budget": example.execution_budget,
        "execution_status": execution.status,
        "execution_steps": execution.steps,
        "observation_budget": example.observation_budget,
        "observation_status": "not run",
        "observation_steps": 0,
    }
    if example.exhausts:
        record["passed"] = execution.status == "exhausted"
        # Never run the unbounded source path on an expected divergence case.
        record["source_result"] = "not run (expected budget exhaustion)"
    else:
        source_result = evaluate(example.expression)
        record["source_result"] = source_data(source_result.value)
        if execution.completed:
            observation = observe(execution.value, example.kind, example.observation_budget)
            record.update(observation_status=observation.status,
                          observation_steps=observation.steps, decoded=observation.value)
            if observation.message:
                record["observation_message"] = observation.message
        record["passed"] = (
            record["source_result"] == example.expected
            and record["observation_status"] == "completed"
            and record.get("decoded") == example.expected
        )
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("MySolution/results"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for example in required_examples():
        record = run_example(example, args.output)
        records.append(record)
        print(json.dumps(record, indent=2), flush=True)
    (args.output / "summary.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    passed = sum(record["passed"] for record in records)
    print(f"{passed}/{len(records)} demonstrations passed. Exhaustion is not proof of nontermination.")
    return 0 if passed == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
