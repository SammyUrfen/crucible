# Crucible Phase 0 pilot targets — throwaway harness (docs/09-roadmap.md, Phase 0).
# The real `make gate` arrives in Phase 1; do not grow this file into it.

# Bibek's pre-made conda env. Called by absolute path because `conda run`
# breaks interactive stdin/$EDITOR passthrough.
PY := /home/SammyUrfen/miniconda3/envs/crucible/bin/python
PILOT := $(PY) pilot/pilot.py

.PHONY: help list lesson review verify verify-quick status lint

help:
	@echo "make list                 lessons + pass state"
	@echo "make lesson ID=<id>       run a lesson (teach -> test)"
	@echo "make review ID=<id>       test-first, reveal-on-miss"
	@echo "make verify [ID=<id>]     prove lessons gradeable (runs all Go references)"
	@echo "make verify-quick [ID=..] structural checks only"
	@echo "make status               streak + honest numbers"
	@echo "make lint                 ruff + mypy on the pilot harness"

list:
	@$(PILOT) list

lesson:
	@$(PILOT) run $(ID)

review:
	@$(PILOT) run $(ID) --review

verify:
	@$(PILOT) verify $(ID)

verify-quick:
	@$(PILOT) verify --quick $(ID)

status:
	@$(PILOT) status

lint:
	@$(PY) -m ruff check pilot/pilot.py
	@$(PY) -m mypy --strict pilot/pilot.py
