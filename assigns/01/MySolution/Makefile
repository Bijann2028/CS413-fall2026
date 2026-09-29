# Makefile for CS413 Assignment 01

all: run_python

# Build and run primary ATS implementation
build_ats:
patscc -o queen queen.dats

run_ats: build_ats
./queen

# Build and run ATS test suite
build_ats_tests:
patscc -o test_queen_ats test_queen.dats

run_ats_tests: build_ats_tests
./test_queen_ats

# Run Python implementation and tests
run_python:
python3 queen.py

run_python_tests:
python3 test_queen.py

clean:
rm -f queen test_queen_ats queen_dats.c test_queen_dats.c
