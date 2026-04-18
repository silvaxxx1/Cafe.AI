.PHONY: test evals

test:
	cd python_code/api && \
	python -m pytest tests/ -v

evals:
	cd python_code/api && \
	python -m tests.evals.eval_guard && \
	python -m tests.evals.eval_classification && \
	python -m tests.evals.eval_recommendation
