FROM python:3.12-alpine3.21

ENV PYTHONBUFFERED=1 \
    DJANGO_DEBUG=False \
    SERVER_ADDRESS=0.0.0.0:8080 \
    SERVER_PORT=8080

WORKDIR /usr/src/app

COPY requirements/prod.txt ./requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "cd /usr/src/app/promo_code && python manage.py migrate --noinput && gunicorn promo_code.wsgi:application --bind ${SERVER_ADDRESS}"]

EXPOSE ${SERVER_PORT}
