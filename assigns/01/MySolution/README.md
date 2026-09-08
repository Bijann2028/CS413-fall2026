# CS413 Assignment #1: GitHub Repository and AI-Assisted Code Translation

This repository contains the original ATS implementation of the Eight-Queens puzzle solver (`queen.dats`), its Python 3 translation (`queen.py`), test verification suites (`test_queen.py`), and documentation of the translation process.

---

## Repository Structure

- `queen.dats`: Original Eight-Queens solver written in ATS2.
- `queen.py`: Translated Eight-Queens solver in Python 3.
- `test_queen.py`: Unit test suite testing top-level functions in Python.
- `AI-TRANSCRIPT.md`: Full transcript of prompts and interactions with Gemini during the translation process.
- `README.md`: Project documentation, build instructions, test case descriptions, and AI reflection.

---

## Build and Execution Instructions

### Prerequisites
- **ATS2 Compiler (`patscc`)**: Required for ATS compilation (typically available in WSL / Linux environments).
- **Python 3**: Required to execute the translated solver and unit test suite.

### 1. Running the Original ATS Implementation

To compile and run `queen.dats` directly using `patscc` in WSL/Linux:

```bash
patscc -o queen queen.dats
./queen

To execute the translated Python solver:
python3 queen.py

To execute the unit tests for top-level functions:
python3 test_queen.py

Description of Tests Performed and Output Comparison
To verify that the translated Python program (queen.py) faithfully preserves the functional logic of the original ATS implementation (queen.dats), tests were conducted targeting every top-level helper function as well as full-program execution.

1. Individual Top-Level Function Unit Tests (test_queen.py)
Board Mutation (board_get, board_set):

Input: Board (0, 0, 0, 0, 0, 0, 0, 0), mutate row 0 to column 4 using board_set.

Expected Result: board_get(board, 0) returns 4.

Output: PASSED

Pairwise Safety Check (safety_test1):

Input A: Queens at (0, 1) and (2, 4) (no column/diagonal conflict). Expected: True.

Input B: Queens at (0, 3) and (2, 3) (same column conflict). Expected: False.

Input C: Queens at (0, 1) and (2, 3) (diagonal conflict). Expected: False.

Output: PASSED

Cumulative Board Safety Check (safety_test2):

Input: Queen placed at (0, 0). Evaluate placing candidate queens on row 1 across columns 0, 1, and 2.

Expected Result: Column 2 is safe (True); Column 0 (vertical) and Column 1 (diagonal) return False.

Output: PASSED

Full Backtracking Search Resolution (search):

Input: Execute search(init_board, 0, 0, 0) from row 0, column 0.

Expected Result: Explores state space and returns total solution count of 92.

Output: PASSED

2. Output Comparison Between ATS and Python
Both executables (queen binary and queen.py) redirect their terminal outputs to text files (ats_output.txt and py_output.txt).

Total Solutions: Both programs reported exactly 92 solutions.

First Solution Board:

ATS Output: Solution #1: (0, 4, 7, 5, 2, 6, 1, 3)

Python Output: Solution #1: (0, 4, 7, 5, 2, 6, 1, 3)

Cross-Language Verification: A file comparison (diff -u ats_output.txt py_output.txt) confirmed 100% character-for-character equivalence across all 92 board configurations.


AI Reflection
From my perspective, Gemini performed very well throughout this code translation task. The original ATS implementation uses static functional constructs, tuples, and explicit tail-recursive helper functions that can be tricky to map directly into dynamic languages. Gemini produced a syntactically clean and logic-accurate Python translation on the first pass, accurately preserving all top-level functions (board_get, board_set, safety_test1, safety_test2, search) and board tuple structures.

The only functional modification I had to make was adding sys.setrecursionlimit(20000) to the top of queen.py. Python’s default call stack limit (1,000) causes a RecursionError during deep backtracking search because Python lacks ATS’s native Tail-Call Optimization (TCO). This adjustment was not an error on Gemini’s part, but rather an environment-specific runtime limitation of Python that required explicit handling.

I had to understand most of the ATS code myself to properly inspect and verify the translation. While the AI-generated unit test cases helped confirm that helper functions behaved identically, the AI version could not have been trusted without manual verification. Although the core translation logic was correct, it initially lacked the necessary recursion depth configuration required to complete the full search without crashing. Utilizing AI definitely decreased the total amount of manual boilerplate coding work I had to do, but human oversight and deep domain understanding remained essential to ensuring a fully working deliverable.