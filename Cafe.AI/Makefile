.PHONY: test evals

test:
	cd coffee_shop_customer_service_chatbot/python_code/api && \
	python -m pytest tests/ -v

evals:
	cd coffee_shop_customer_service_chatbot/python_code/api && \
	python -m tests.evals.eval_guard && \
	python -m tests.evals.eval_classification && \
	python -m tests.evals.eval_recommendation
