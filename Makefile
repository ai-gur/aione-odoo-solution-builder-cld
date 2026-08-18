# Convenience wrapper. The canonical implementation is scripts/run.py, because
# `make` is not present on a stock Windows machine and this project's first
# developers are on Windows. Both entry points run the same commands.
#
#   python scripts/run.py <command>
#   make <command>

RUN := python scripts/run.py

.PHONY: help bootstrap stack-up stack-down stack-ps db-migrate db-status db-reset         test test-contract test-integration test-api api-dev worker-dev

help:
	@$(RUN)

bootstrap:        ; $(RUN) bootstrap
stack-up:         ; $(RUN) stack-up
stack-down:       ; $(RUN) stack-down
stack-ps:         ; $(RUN) stack-ps
db-migrate:       ; $(RUN) db-migrate
db-status:        ; $(RUN) db-status
db-reset:         ; $(RUN) db-reset
test:             ; $(RUN) test
test-contract:    ; $(RUN) test-contract
test-integration: ; $(RUN) test-integration
test-api:         ; $(RUN) test-api
api-dev:          ; $(RUN) api-dev
worker-dev:       ; $(RUN) worker-dev
