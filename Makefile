.PHONY: test test_python3

test: test_python3

test_python3:
	@echo ">>Runnning tests in Python 3"
	@python3 -m pytest
	@echo
