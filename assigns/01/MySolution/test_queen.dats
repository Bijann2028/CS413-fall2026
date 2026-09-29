#include "share/atspre_staload.hats"

// Static load queen.dats into scope
staload "queen.dats"

// Dynamic load queen.dats implementation code
dynload "queen.dats"

fun assert_test (name: string, cond: bool): void =
  if cond then
    println! ("[PASS] ", name)
  else
    println! ("[FAIL] ", name)

implement main0 () = let
  val init_bd = (0, 0, 0, 0, 0, 0, 0, 0)

  // Test 1: board_set and board_get
  val bd_mod = board_set (init_bd, 0, 4)
  val val_0 = board_get (bd_mod, 0)
  val () = assert_test ("board_get/set row 0", val_0 = 4)

  // Test 2: safety_test1
  val safe_pair = safety_test1 (0, 1, 2, 4)
  val unsafe_col = safety_test1 (0, 3, 2, 3)
  val () = assert_test ("safety_test1 valid pair", safe_pair = true)
  val () = assert_test ("safety_test1 same column conflict", unsafe_col = false)

  // Test 3: safety_test2
  val bd_queen0 = board_set (init_bd, 0, 0)
  val safe_placement = safety_test2 (1, 2, bd_queen0, 0)
  val unsafe_placement = safety_test2 (1, 0, bd_queen0, 0)
  val () = assert_test ("safety_test2 valid placement", safe_placement = true)
  val () = assert_test ("safety_test2 conflict placement", unsafe_placement = false)

  // Test 4: Full search total count check
  val total = search (init_bd, 0, 0, 0)
  val () = assert_test ("search total 92 solutions", total = 92)

in
  println! ("ATS top-level tests defined successfully.")
end
