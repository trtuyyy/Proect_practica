# Dockerfile
# Стоматологическая клиника — Plotly Dash Dashboard
# Используется для Trivy-анализа безопасности

FROM python:3.11-slim

# Метаданные
LABEL maintainer="dental-clinic-vkr"
LABEL description="Аналитический дашборд стоматологической клиники"
LABEL version="1.0"

# Не запускаем от root (безопасность)
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY app.py .

# Меняем владельца файлов
RUN chown -R appuser:appuser /app

# Переключаемся на non-root
USER appuser

EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050')" || exit 1

CMD ["python", "app.py"]
