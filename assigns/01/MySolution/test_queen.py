import unittest
import sys
import io

# Import top-level functions from your translated solver
from queen import (
    board_get,
    board_set,
    safety_test1,
    safety_test2,
    search
)

class TestQueenTopLevelFunctions(unittest.TestCase):

    def test_board_get_and_set(self):
        """Test tuple getter and setter operations across various rows."""
        initial_board = (0, 0, 0, 0, 0, 0, 0, 0)
        
        # Test board_set and board_get on boundary rows
        updated_board_0 = board_set(initial_board, 0, 4)
        self.assertEqual(board_get(updated_board_0, 0), 4)
        
        updated_board_7 = board_set(initial_board, 7, 6)
        self.assertEqual(board_get(updated_board_7, 7), 6)

    def test_safety_test1(self):
        """Test pairwise safety conflicts (same column, same diagonal, safe placement)."""
        # Same column -> Unsafe
        self.assertFalse(safety_test1(0, 3, 2, 3))
        
        # Same diagonal -> Unsafe
        self.assertFalse(safety_test1(0, 2, 2, 4))
        
        # Safe placement -> Safe
        self.assertTrue(safety_test1(0, 1, 2, 4))

    def test_safety_test2(self):
        """Test safety of placing a queen against an existing board configuration."""
        # Board with Queen at row 0, col 0
        board = (0, 0, 0, 0, 0, 0, 0, 0)
        
        # Placing a queen at row 1, col 0 (same column as row 0) -> Unsafe
        self.assertFalse(safety_test2(1, 0, board, 0))
        
        # Placing a queen at row 1, col 1 (diagonal with row 0) -> Unsafe
        self.assertFalse(safety_test2(1, 1, board, 0))
        
        # Placing a queen at row 1, col 2 -> Safe relative to row 0
        self.assertTrue(safety_test2(1, 2, board, 0))

    def test_search_full_execution(self):
        """Test that the full search algorithm identifies exactly 92 solutions."""
        sys.setrecursionlimit(20000)
        empty_board = (0, 0, 0, 0, 0, 0, 0, 0)
        
        # Suppress printed outputs during test execution
        suppress_output = io.StringIO()
        sys.stdout = suppress_output
        try:
            total_solutions = search(empty_board, 0, 0, 0)
        finally:
            sys.stdout = sys.__stdout__
            
        self.assertEqual(total_solutions, 92)

if __name__ == "__main__":
    unittest.main()
