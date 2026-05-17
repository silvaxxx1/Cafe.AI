.PHONY: test test-frontend test-all evals

test:
	cd python_code/api && \
	python -m pytest tests/ -v

test-frontend:
	cd coffee_shop_app && \
	npx jest --watchAll=false --no-coverage

test-all: test test-frontend

evals:
	cd python_code/api && \
	python -m tests.evals.eval_guard && \
	python -m tests.evals.eval_classification && \
	python -m tests.evals.eval_recommendation
