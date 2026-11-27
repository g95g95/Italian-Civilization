# Civ Italia build. `make all` reruns everything from the raw downloads; each phase ends with its gate.
PY := python3
S := scripts

.PHONY: all download phase1 phase2 phase3 phase4 phase5 phase6 test serve clean sources

all: phase6

download:
	cd $(S) && $(PY) download.py

phase1: download
	cd $(S) && $(PY) crosswalk.py
	$(PY) -m pytest -q -m phase1

phase2: phase1
	cd $(S) && $(PY) grid.py
	cd $(S) && $(PY) socio.py   # residents per tile are needed by the phase-2 gate
	$(PY) -m pytest -q -m phase2

phase3: phase2
	cd $(S) && $(PY) elections.py && $(PY) political.py
	$(PY) -m pytest -q -m phase3

phase4: phase3
	$(PY) -m pytest -q -m phase4

phase5: phase4
	cd $(S) && $(PY) terrain.py && $(PY) layers.py && $(PY) socio.py
	$(PY) -m pytest -q -m phase5

phase6: phase5 sources
	cd $(S) && $(PY) export.py
	$(PY) -m pytest -q -m phase6

sources:
	cd $(S) && $(PY) sources_md.py

test:
	$(PY) -m pytest -q

serve:
	cd web && $(PY) -m http.server 8000

clean:
	rm -rf data/processed web/data
