FROM python:3.11-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/devices.db

EXPOSE 5236

RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "server.py"]