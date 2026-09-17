.PHONY: api web studio cli test

api:
	uvicorn api.main:app --reload

web:
	cd web && npm run dev

studio:
	langgraph dev

cli:
	python main.py

test:
	pytest
