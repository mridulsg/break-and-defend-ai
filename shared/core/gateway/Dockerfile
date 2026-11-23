# Base image pinned by digest (python:3.12-slim). Update deliberately, not by floating tag.
FROM python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin gateway \
 && mkdir /data && chown gateway:gateway /data

WORKDIR /app

# Every dependency is hash-pinned; pip refuses anything that does not match.
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY app.py models.json ./

USER gateway
EXPOSE 4000
LABEL bdai.component="core"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "4000", "--no-access-log"]
