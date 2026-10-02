.PHONY: build up down logs test

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f api processor

test:
	pytest -q hard/hw3/tests/tests.py
