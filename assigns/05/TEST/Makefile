NODE ?= node
PYTHON ?= python3

.PHONY:: test
.PHONY:: test-js
.PHONY:: test-py

test:: test-js
test:: test-py

test-js:
	$(NODE) --test test_lambda1_vp.js

test-py:
	$(PYTHON) -m unittest discover -s . -p 'test_*.py' -v

