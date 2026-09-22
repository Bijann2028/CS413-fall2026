import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from queens_lambda0 import cons, count_solutions, find_one_solution, is_valid_board, make_queens_term, make_safe, nil
from lambda0 import T0Mbtf, T0Mint, t0erm_cbv_evaluate0, t0erm_fvset, T0Mapp

def apply3(fn, a, b, c):
    return T0Mapp(T0Mapp(T0Mapp(fn, a), b), c)

class TestQueensTranslation(unittest.TestCase):
    def test_conflict_checker(self):
        self.assertTrue(is_valid_board((1, 3, 0, 2)))
        self.assertFalse(is_valid_board((0, 1, 2, 3)))       # diagonal conflicts
        self.assertFalse(is_valid_board((0, 2, 0, 3)))       # shared row
        board = cons(T0Mint(0), nil())
        self.assertEqual(t0erm_cbv_evaluate0(apply3(make_safe(), T0Mint(1), board, T0Mint(1))), T0Mbtf(False))
        self.assertEqual(t0erm_cbv_evaluate0(apply3(make_safe(), T0Mint(3), board, T0Mint(1))), T0Mbtf(True))
    def test_program_is_closed(self):
        self.assertEqual(t0erm_fvset(make_queens_term(4)), frozenset())
    def test_small_boards(self):
        self.assertEqual(count_solutions(1), 1)
        self.assertEqual(count_solutions(4), 2)
    def test_eight_queens(self):
        self.assertEqual(count_solutions(8), 92)
        board = find_one_solution(8)
        self.assertEqual(len(board), 8)
        self.assertTrue(is_valid_board(board))

if __name__ == '__main__': unittest.main(verbosity=2)
