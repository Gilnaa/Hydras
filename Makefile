.PHONY: test test_python2 test_python3

test: test_python2 test_python3

test_python2:
	@echo ">> Running tests in Python 2"
	@python2 tests/all.py
	@echo

test_python3:
	@echo ">>Runnning tests in Python 3"
	@python3 tests/all.py
	@echo
