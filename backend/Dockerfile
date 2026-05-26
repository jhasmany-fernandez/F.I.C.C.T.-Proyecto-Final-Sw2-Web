FROM python:3.12-slim AS base
WORKDIR /app

FROM base AS builder
RUN pip install --upgrade pip
COPY pyproject.toml .
RUN pip install --no-cache-dir ".[dev]"
COPY app ./app

FROM base AS final
RUN useradd --no-create-home --shell /bin/false appuser
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic
COPY --from=builder /app/app ./app
COPY alembic.ini .
COPY alembic ./alembic
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
