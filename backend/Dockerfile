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
RUN pip install --no-cache-dir gunicorn whitenoise

# کپی پروژه
COPY . .

# تنظیم محیط
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV PYTHONUNBUFFERED=1

# مهاجرت و اجرا
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
