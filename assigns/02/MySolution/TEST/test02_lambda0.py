import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lambda0 import *

class TestPairs(unittest.TestCase):
    def test_size_and_free_variables(self):
        term = T0Mpfst(T0Mpair(T0Mvar('x'), T0Mpsnd(T0Mpair(T0Mint(1), T0Mvar('y')))))
        self.assertEqual(t0erm_size(term), 7)
        self.assertEqual(t0erm_fvset(term), frozenset({'x', 'y'}))
    def test_substitution_and_binders(self):
        term = T0Mpair(T0Mvar('x'), T0Mpfst(T0Mvar('x')))
        self.assertEqual(t0erm_subst0(term, 'x', T0Mint(4)), T0Mpair(T0Mint(4), T0Mpfst(T0Mint(4))))
        self.assertEqual(t0erm_subst0(T0Mlam('x', term), 'x', T0Mint(4)), T0Mlam('x', term))
        self.assertEqual(t0erm_subst0(T0Mfix('f', 'x', term), 'x', T0Mint(4)), T0Mfix('f', 'x', term))
        self.assertEqual(
            t0erm_subst0(T0Mlam('y', T0Mpair(T0Mvar('x'), T0Mvar('y'))), 'x', T0Mint(4)),
            T0Mlam('y', T0Mpair(T0Mint(4), T0Mvar('y'))),
        )
        self.assertEqual(
            t0erm_subst0(T0Mfix('f', 'y', T0Mpfst(T0Mvar('x'))), 'x', T0Mint(4)),
            T0Mfix('f', 'y', T0Mpfst(T0Mint(4))),
        )
    def test_evaluation_and_projections(self):
        pair = T0Mpair(T0Mop2('+', T0Mint(2), T0Mint(3)), T0Mlam('x', T0Mvar('x')))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpfst(pair)), T0Mint(5))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpsnd(pair)), T0Mlam('x', T0Mvar('x')))
        nested = T0Mpair(T0Mint(1), T0Mpair(T0Mbtf(True), T0Mstr('ok')))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mpfst(T0Mpsnd(nested))), T0Mbtf(True))
    def test_functions_and_errors(self):
        get_second = T0Mlam('p', T0Mpsnd(T0Mvar('p')))
        self.assertEqual(t0erm_cbv_evaluate0(T0Mapp(get_second, T0Mpair(T0Mint(3), T0Mint(9)))), T0Mint(9))
        with self.assertRaises(TypeError): t0erm_cbv_evaluate0(T0Mpfst(T0Mint(1)))
        with self.assertRaises(ZeroDivisionError):
            t0erm_cbv_evaluate0(T0Mpfst(T0Mpair(T0Mint(1), T0Mop2('/', T0Mint(1), T0Mint(0)))))

if __name__ == '__main__': unittest.main(verbosity=2)
