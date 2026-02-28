.PHONY: test verify

test:
	python3 -m pytest -q

verify:
	bash scripts/verify.sh
