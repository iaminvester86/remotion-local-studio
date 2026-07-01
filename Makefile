# Convenience targets. Requires the venv to exist (run ./install.sh first).
VENV=.venv
PY=$(VENV)/bin/python

.PHONY: install doctor image music video clean

install:
	./install.sh

doctor:
	$(PY) -m rls doctor

image:
	$(PY) -m rls install image

music:
	$(PY) -m rls install music

video:
	$(PY) -m rls install video

clean:
	rm -rf .cache __pycache__ rls/__pycache__ rls/tools/__pycache__
