.PHONY: config up down logs test-backend test-frontend

config:
	docker-compose config

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

