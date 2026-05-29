# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/synthlog /usr/local/bin/synthlog
COPY src/ src/

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["synthlog"]
CMD ["generate"]
