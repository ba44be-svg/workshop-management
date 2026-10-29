FROM python:3.12-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# کپی requirements و نصب
COPY requirements_local.txt .
RUN pip install --no-cache-dir -r requirements_local.txt
RUN pip install --no-cache-dir gunicorn whitenoise dj-database-url psycopg2-binary

# کپی پروژه
COPY . .

# تنظیم محیط
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV PYTHONUNBUFFERED=1

# collectstatic — اگه خطا داد، ادامه بده (اختیاری)
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# ایجاد پوشه staticfiles اگه نبود
RUN mkdir -p staticfiles

EXPOSE 8000

# اجرای migrate + collectstatic + gunicorn در زمان شروع
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput 2>/dev/null || true && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
