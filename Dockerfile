# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir ".[server]"

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/synthlog /usr/local/bin/synthlog
COPY src/ src/

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

ENTRYPOINT ["synthlog"]
CMD ["serve", "--port", "8080"]
