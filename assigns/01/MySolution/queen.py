import sys
sys.setrecursionlimit(20000)

# Constants
N = 8

# Functions for printing
def print_dots(i: int) -> None:
    if i > 0:
        print(". ", end="")
        print_dots(i - 1)

def print_row(i: int) -> None:
    print_dots(i)
    print("Q ", end="")
    print_dots(N - i - 1)
    print()

def print_board(bd: tuple) -> None:
    print_row(bd[0])
    print_row(bd[1])
    print_row(bd[2])
    print_row(bd[3])
    print_row(bd[4])
    print_row(bd[5])
    print_row(bd[6])
    print_row(bd[7])
    print()

def board_get(bd: tuple, i: int) -> int:
    if i == 0: return bd[0]
    elif i == 1: return bd[1]
    elif i == 2: return bd[2]
    elif i == 3: return bd[3]
    elif i == 4: return bd[4]
    elif i == 5: return bd[5]
    elif i == 6: return bd[6]
    elif i == 7: return bd[7]
    else: return -1

def board_set(bd: tuple, i: int, j: int) -> tuple:
    bd_list = list(bd)
    if 0 <= i < 8:
        bd_list[i] = j
        return tuple(bd_list)
    return bd

def safety_test1(i0: int, j0: int, i1: int, j1: int) -> bool:
    return j0 != j1 and abs(i0 - i1) != abs(j0 - j1)

def safety_test2(i0: int, j0: int, bd: tuple, i: int) -> bool:
    if i >= 0:
        if safety_test1(i0, j0, i, board_get(bd, i)):
            return safety_test2(i0, j0, bd, i - 1)
        else:
            return False
    else:
        return True

def search(bd: tuple, i: int, j: int, nsol: int) -> int:
    if j < N:
        test = safety_test2(i, j, bd, i - 1)
        if test:
            bd1 = board_set(bd, i, j)
            if i + 1 == N:
                print(f"Solution #{nsol + 1}:\n")
                print_board(bd1)
                # Fixed: Pass bd1 instead of bd so row 7 retains its placed column during backtracking
                return search(bd1, i, j + 1, nsol + 1)
            else:
                return search(bd1, i + 1, 0, nsol)
        else:
            return search(bd, i, j + 1, nsol)
    else:
        if i > 0:
            return search(bd, i - 1, board_get(bd, i - 1) + 1, nsol)
        else:
            return nsol

if __name__ == "__main__":
    init_bd = (0, 0, 0, 0, 0, 0, 0, 0)
    total = search(init_bd, 0, 0, 0)
    print(f"Total number of solutions: {total}")