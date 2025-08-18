#!/bin/sh

# Путь к файлу-флагу для проверки загрузки фикстур
FLAG_FILE=/app/fixtures_loaded.flag

# Проверка на существование файл-флага
if [ ! -f "$FLAG_FILE" ]; then
    until cd /app
    do
        echo "Waiting for server volume..."
    done

    if [ "$DATABASE" = "postgres" ]; then
        while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
            sleep 0.1
        done
        echo "POSTGRES READY"
    fi

    # Создание миграций
    python manage.py makemigrations


    # Миграция
    python manage.py migrate

    # Сбор статических файлов
    python manage.py collectstatic --noinput

    # Загрузка фикстур
    ./manage.py loaddata fixtures/Link.json --app Link

    # Создание файл-флага, указывающий на то, что фикстуры были загружены
    touch $FLAG_FILE
fi

# Запуск сервера Django
nohup python manage.py runserver 0.0.0.0:8000