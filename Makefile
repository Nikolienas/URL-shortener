# Основные команды
init: docker-down-clear docker-pull docker-build docker-up
migrate-data: makemigrate migrate
down: docker-down-clear
restart: down init

# Докер

docker-up:
	docker-compose up

docker-down:
	docker-compose down --remove-orphans

docker-down-clear:
	docker-compose down -v --remove-orphans

docker-pull:
	docker-compose pull

docker-build:
	docker-compose build

# Джанго

makemigrate:
	docker exec django_url_shortener python manage.py makemigrations

migrate:
	docker exec django_url_shortener python manage.py migrate

createsuperuser:
	python $(PWD)/src/backend/manage.py createsuperuser