.PHONY: test pytest examples

test: pytest examples

pytest:
	@python3 -m pytest

examples:
	@for exa in $$(find examples -type f); do echo "$$exa"; PYTHONPATH=. python3 $$exa || exit 1; done