# Canonical developer commands (LOCAL-DEVELOPMENT.md).
# README and CI use this interface and no other.

.PHONY: help bootstrap check test test-contract test-contract-ts test-contract-py

help:
	@echo "bootstrap       install toolchains and dependencies"
	@echo "check           format, lint and type checks"
	@echo "test            all tests"
	@echo "test-contract   shared contract tests in both ecosystems"

bootstrap:
	pnpm install
	cd packages/contracts/python && uv sync

check:
	@echo "no checks wired yet"

test: test-contract

# Both suites read the same fixtures. Passing here and there is what proves the
# TypeScript and Python canonicalizers agree byte for byte (ADR-015).
test-contract: test-contract-ts test-contract-py

test-contract-ts:
	node --test packages/contracts/ts/test/*.test.ts

test-contract-py:
	cd packages/contracts/python && PYTHONPATH=. python -m unittest discover -s tests
