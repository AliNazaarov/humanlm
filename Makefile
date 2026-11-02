PYTHON ?= python3

eval:       ## score committed outputs, write hackathon/report/results.json + RESULTS.md
	$(PYTHON) hackathon/eval/score_all.py
test:       ## metric + stats unit tests
	cd pipeline && $(PYTHON) -m unittest tests.test_metrics
	$(PYTHON) -m unittest discover -s hackathon/eval -p "test_*.py"
