# Assignment 5: testing and requirement coverage

## Verification environment

Verified October 12, 2026, on Windows with Python 3.12.10 and pytest 9.1.1.
Commands below run from `assigns/05/`, following README setup.

| Suite | Command | Observed result |
| --- | --- | --- |
| Required unittest | `.\.venv\Scripts\python.exe -m unittest discover -s MySolution/TEST -p "test_*_unittest.py" -v` | 6 test methods passed; fixture checks use subtests |
| Required pytest | `.\.venv\Scripts\python.exe -m pytest MySolution/TEST/test_visitors_pytest.py -v` | 152 tests passed |
| Supplied interpreter regression | `.\.venv\Scripts\python.exe -m unittest discover -s TEST -p "test_*.py" -v` | 74 tests passed |

The required suites run independently. Pytest targets its own functions and
plain assertions, rather than collecting the unittest suite. Shared fixtures
contain 18 explicit printing expectations and 44 explicit substitution
expectations; expected outputs are not computed by the implementation.

## Requirement mapping

Both suites use the following test names (unittest methods or pytest functions).

| Check | Tests and fixtures |
| --- | --- |
| T1: exact printing | `test_exact_printing`: all 13 constructors, nesting, negative and 81-digit integers, true and false |
| T2: substitution | `test_substitution_scope_and_capture`: every constructor, matching/nonmatching variables, single insertion of a replacement containing the target |
| T3: shadowing | Lambda, function/parameter fix binding, equal fix names, and let shadow fixtures |
| T4: capture avoidance | Lambda, let, individual fix binders, both distinct fix binders, and equal fix binders |
| T5: renaming/freshness | Nested lambda, fix and let shadowing; existing free names, unused binders, replacement binders, target names, and earlier generated names |
| T6: let scope | Initializer substitution under a target-binding let; renamed body with unchanged free initializer spelling; nested let initializer under an outer binder |
| T7: preservation/determinism | `test_preservation_and_determinism` checks both ASTs against deep copies and compares repeated results; printing also checks preservation |
| T7: non-evaluation | `test_no_evaluation` replaces the supplied evaluator function and visitor with failures; division-by-zero fixtures still print and substitute |
| T8: free-variable property | `test_free_variable_property` checks the equation on all 44 substitution fixtures; exact outputs are separately checked |
| T9: absent target | Same property test requires structural equality for absent targets; fixtures also check avoidance of unnecessary renaming |
| Visitor dispatch | `test_direct_visitor_dispatch_and_replacement_identity` checks interface instances, direct accept calls, and exact replacement object insertion |

## Review

Reviewed visitor methods against the supplied constructor fields and print
format. Reviewed renaming boundaries at lambdas, both fix declarations, and
let initializers/bodies. All expression traversal uses visitors; no central
type/tag dispatch or evaluator call is used. Substitution reserves names from
both original inputs before generating any names, and uses independent state
for each entry-point call. The supplied interpreter files were not edited.

The README's three Python demonstration expressions were executed with their
documented expected outputs. The design explanation is within 300–500 words.
Git whitespace checks passed. Local environment and cache directories are
ignored and are not submission files.
