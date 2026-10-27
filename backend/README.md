# نرم‌افزار جامع مدیریت تولید و پخش — v2.0

> سیستم مدیریت تولید، انبار، فروش و حسابداری

## 📦 محتویات

```
django_starter/
├── backend/
│   ├── config/
│   │   ├── settings/          # Settings (base/development/production)
│   │   ├── urls.py            # Root URL configuration
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/                  # ۱۷ Django App
│   │   ├── accounts/          # کامل با models, views, serializers, signals
│   │   ├── products/          # اسکلت
│   │   ├── inventory/
│   │   ├── production/
│   │   ├── dispatch/
│   │   ├── sales/
│   │   ├── transfers/
│   │   ├── partners/
│   │   ├── accounting/
│   │   ├── notifications/
│   │   ├── reports/
│   │   ├── approval_workflow/  # جدید v2
│   │   ├── store_portal/        # جدید v2
│   │   ├── payments/            # جدید v2
│   │   ├── loyalty/             # جدید v2
│   │   ├── barcode/             # جدید v2
│   │   └── saman_tax/           # جدید v2
│   └── core/                  # Shared utilities
│       ├── middleware.py     # RBAC, ActivityLog
│       ├── permissions.py     # RBAC Permissions
│       ├── models.py          # BaseModel (Soft Delete)
│       ├── exceptions.py      # Custom API exceptions
│       ├── tasks.py           # Celery tasks
│       └── health_urls.py     # Health check endpoints
├── deploy/
│   ├── docker/
│   │   └── Dockerfile.backend
│   └── nginx/
│       └── nginx.conf
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions CI/CD
├── docker-compose.yml          # 7 services
├── manage.py
├── requirements.txt
├── .env.example
└── README.md                   # این فایل
```

## 🚀 شروع سریع

### روش ۱: با Docker Compose (توصیه می‌شود)

```bash
# ۱. کلون کن
git clone <repository-url>
cd django_starter

# ۲. متغیرهای محیطی
cp .env.example .env
# ویرایش .env و تنظیم مقادیر واقعی

# ۳. راه‌اندازی سرویس‌ها
docker compose up -d

# ۴. صبر کن ۳۰ ثانیه تا سرویس‌ها ready بشن

# ۵. اجرای migrationها (می‌تونی از پوشه sql_migrations استفاده کنی)
docker compose exec backend python manage.py migrate

# ۶. ساخت superuser
docker compose exec backend python manage.py createsuperuser

# ۷. جمع‌آوری static files
docker compose exec backend python manage.py collectstatic --noinput

# ۸. بررسی سلامت
curl http://localhost:8000/api/health/
```

### روش ۲: Development محلی (بدون Docker)

```bash
# ۱. ساخت virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا venv\Scripts\activate  # Windows

# ۲. نصب وابستگی‌ها
pip install -r requirements.txt

# ۳. تنظیم environment
cp .env.example .env
# ویرایش .env با مقادیر local (postgres/redis روی localhost)

# ۴. اجرای migration
python manage.py migrate

# ۵. ساخت superuser
python manage.py createsuperuser

# ۶. اجرای development server
python manage.py runserver

# ۷. در terminal دیگر، Celery worker را اجرا کن
celery -A config worker -l info

# ۸. و Celery beat برای scheduled tasks
celery -A config beat -l info
```

## 🌐 دسترسی‌ها

پس از راه‌اندازی، این URLها در دسترس هستند:

| URL | شرح |
|-----|------|
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/api/docs/ | Swagger UI (API Documentation) |
| http://localhost:8000/api/redoc/ | ReDoc (Alternative API Docs) |
| http://localhost:8000/api/schema/ | OpenAPI Schema (JSON) |
| http://localhost:8000/api/health/ | Health Check |
| http://localhost:5555/ | Flower (Celery Monitoring) |
| http://localhost:15672/ | RabbitMQ Management (guest/guest) |
| http://localhost:9001/ | MinIO Console |

## 📊 ۱۷ Django App

### Apps اصلی (از نسخه ۱.۰)
| # | App | شرح | وضعیت |
|---|------|------|------|
| ۱ | `accounts` | کاربران و نقش‌ها | ✅ کامل |
| ۲ | `products` | محصولات و دسته‌بندی | 📋 اسکلت |
| ۳ | `inventory` | انبار و موجودی | 📋 اسکلت |
| ۴ | `production` | تولید و مصرف | 📋 اسکلت |
| ۵ | `dispatch` | پخش و بارگیری | 📋 اسکلت |
| ۶ | `sales` | فروش و برگشت | 📋 اسکلت |
| ۷ | `transfers` | انتقال بین فروشگاه‌ها | 📋 اسکلت |
| ۸ | `partners` | فروشگاه‌ها و عوامل | 📋 اسکلت |
| ۹ | `accounting` | حسابداری دوطرفه | 📋 اسکلت |
| ۱۰ | `notifications` | اعلان و پیامک | 📋 اسکلت |
| ۱۱ | `reports` | گزارش و داشبورد | 📋 اسکلت |

### Apps جدید (نسخه ۲.۰)
| # | App | شرح | وضعیت |
|---|------|------|------|
| ۱۲ | `approval_workflow` | جریان تأیید مدیر | 📋 اسکلت |
| ۱۳ | `store_portal` | پورتال فروشگاه PWA | 📋 اسکلت |
| ۱۴ | `payments` | پرداخت آنلاین (۳ درگاه) | 📋 اسکلت |
| ۱۵ | `loyalty` | وفاداری + Smart Reorder | 📋 اسکلت |
| ۱۶ | `barcode` | بارکد و QR Code | 📋 اسکلت |
| ۱۷ | `saman_tax` | صورت‌حساب الکترونیکی | 📋 اسکلت |

## 🛠️ ساختار هر App

هر App با الگوی زیر توسعه پیدا می‌کنه:

```
app_name/
├── __init__.py
├── apps.py              # AppConfig
├── models.py            # Django models
├── serializers.py       # DRF serializers
├── views.py             # ViewSets / APIViews
├── urls.py              # URL routing
├── admin.py             # Django admin configuration
├── signals.py           # Django signals (اختیاری)
├── services/            # Business logic
│   └── *_service.py
├── repositories/        # Data access layer (اختیاری)
├── tasks.py             # Celery tasks (اختیاری)
├── selectors.py         # Complex queries (اختیاری)
└── tests/               # Test modules
    ├── test_models.py
    ├── test_services.py
    └── test_api.py
```

> نکته: فایل `accounts` به‌عنوان نمونه کامل (با تمام لایه‌ها) پیاده‌سازی شده. سایر App‌ها در فاز ۱ توسعه، با همین الگو تکمیل می‌شوند.

## 🔐 RBAC و نقش‌ها

سیستم ۵ نقش اصلی دارد:

| نقش | دسترسی‌ها |
|------|------|
| `manager` | دسترسی کامل + تأیید/رد اسناد |
| `accountant` | سند حسابداری + گزارش‌های مالی + تأیید پرداخت‌ها |
| `storekeeper` | ثبت تولید و حرکت انبار |
| `distributor` | ثبت پیش‌نویس فروش + اسکن بارکد |
| `store_owner` | سفارش آنلاین + پرداخت + گزارش |

برای اضافه کردن permission به یک view:
```python
from core.permissions import IsManager, IsManagerOrAccountant
from rest_framework.permissions import IsAuthenticated

class SalesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsManagerOrAccountant]
    ...
```

## 🐳 سرویس‌های Docker

`docker-compose.yml` شامل ۷ سرویس:

| سرویس | پورت | توضیح |
|------|------|------|
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 (Cache + Sessions) |
| `rabbitmq` | 5672, 15672 | RabbitMQ 3 (Celery Broker) |
| `minio` | 9000, 9001 | Object Storage (S3-compatible) |
| `backend` | 8000 | Django + Gunicorn |
| `celery_worker` | - | Celery Workers |
| `celery_beat` | - | Celery Beat (Scheduled) |
| `flower` | 5555 | Celery Monitoring |
| `nginx` | 80, 443 | Reverse Proxy |

## ✅ اوامر مفید

```bash
# ساخت migration
docker compose exec backend python manage.py makemigrations

# اجرای migration
docker compose exec backend python manage.py migrate

# ساخت superuser
docker compose exec backend python manage.py createsuperuser

# جمع‌آوری static files
docker compose exec backend python manage.py collectstatic --noinput

# اجرای تست‌ها
docker compose exec backend pytest

# ساخت dumpdata
docker compose exec backend python manage.py dumpdata accounts > accounts.json

# ورود به shell
docker compose exec backend python manage.py shell

# اجرای Celery worker
docker compose exec backend celery -A config worker -l info

# مشاهده لاگ‌ها
docker compose logs -f backend
docker compose logs -f celery_worker

# restart یک سرویس
docker compose restart backend
```

## 🔗 ارتباط با سایر Artifactها

این پروژه بر اساس سند معماری نسخه ۲.۰ ساخته شده:

| Artifact | مسیر |
|---------|------|
| سند معماری PDF | سند معماری فایل |
| سند معماری HTML | نسخه HTML |
| SQL Migrations | `../sql_migrations/` |
| API Specification | (در فاز C تولید می‌شود) |
| UI Wireframes | (در فاز D تولید می‌شود) |

## 🎯 گام‌های بعدی

1. ✅ فاز A: SQL Migrations — کامل
2. ✅ فاز B: Django Starter — کامل
3. ⏳ فاز C: API Specification (با OpenAPI)
4. ⏳ فاز D: UI Wireframes
5. ⏳ فاز E: Data Dictionary

## 📞 پشتیبانی

برای سؤالات فنی یا گزارش باگ، Issue در GitHub باز کنید.

---

**نسخه:** 2.0.0 | **تاریخ:** 1404 | **توسعه توسط:** تیم ارشد مهندسی نرم‌افزار
