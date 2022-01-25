FROM python:3.8.12-slim-bullseye

COPY . .

RUN pip install -U pip && \
    pip install poetry && \
    poetry export --format requirements.txt --output requirements.txt --without-hashes && \
    pip install -r requirements.txt

CMD python auto_bot/main.py