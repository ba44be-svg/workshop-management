# 📥 راهنمای نصب روی کامپیوتر دیگر

> این راهنما با موفقیت روی Python 3.12 + Node.js 22 تست شده است.

## 🎯 آنچه نصب می‌کنید

| بخش | تکنولوژی | پورت |
|---|---|---|
| بک‌اند | Django 4.2 + DRF + SQLite | 8000 |
| فرانت‌اند | Next.js 16 + React 19 + shadcn/ui | 3000 |

## ۱) پیش‌نیازها

- **Python 3.11 یا 3.12** (نه 3.13+) → از [python.org](https://python.org). هنگام نصب روی ویندوز تیک `Add Python to PATH` را بزنید.
- **Node.js 18+** یا **Bun** → از [nodejs.org](https://nodejs.org) یا [bun.sh](https://bun.sh).
- **Git** (پیشنهادی برای Git Bash روی ویندوز) → از [git-scm.com](https://git-scm.com).

## ۲) دریافت فایل‌های پروژه

فایل `workshop_install_package.tar` را در یک پوشه‌ی دلخواه قرار دهید و سپس:

```bash
mkdir workshop && cd workshop
tar -xf /path/to/workshop_install_package.tar
```

ساختار نهایی:
```
workshop/
├── backend/          ← کد Django
└── frontend/         ← کد Next.js
```

## ۳) نصب خودکار (پیشنهادی)

ساده‌ترین راه، استفاده از اسکریپت خودکار است:

```bash
cd workshop/backend
chmod +x setup_complete.sh
./setup_complete.sh
```

این اسکریپت خودش:
1. venv می‌سازد
2. وابستگی‌های Python را نصب می‌کند
3. `migrate` و `seed_data` را اجرا می‌کند
4. وابستگی‌های فرانت‌اند را نصب می‌کند

برای نصب + اجرای خودکار هر دو سرور:
```bash
./setup_complete.sh --run
```

## ۴) نصب دستی (اگر اسکریپت کار نکرد)

### ۴.۱ — بک‌اند
```bash
cd workshop/backend
python -m venv venv
source venv/bin/activate        # ویندوز: venv\Scripts\activate
pip install -r requirements_local.txt

# بررسی و ایجاد .env اگر نیست
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

### ۴.۲ — فرانت‌اند (در ترمینال جدید)
```bash
cd workshop/frontend
npm install        # یا: bun install
npm run dev        # یا: bun run dev
```

## ۵) حساب‌های کاربری آماده (seed شده)

| نام کاربری | گذرواژه | نقش |
|---|---|---|
| `admin` | `Admin@12345678` | مدیر کل |
| `accountant1` | `Sample@12345678` | حسابدار |
| `storekeeper1` | `Sample@12345678` | انباردار |
| `distributor1` | `Sample@12345678` | عامل پخش |

## ۶) اجرا (پس از نصب)

دو ترمینال باز کنید:

**ترمینال ۱ — بک‌اند:**
```bash
cd workshop/backend
source venv/bin/activate        # ویندوز: venv\Scripts\activate
python manage.py runserver
```

**ترمینال ۲ — فرانت‌اند:**
```bash
cd workshop/frontend
npm run dev
```

**مرورگر:** `http://localhost:3000` → با `admin` / `Admin@12345678` وارد شوید.

## ۷) اشکال‌زدایی

### `ModuleNotFoundError: No module named 'whitenoise'`
```bash
pip install whitenoise==6.7.0
```

### نوار زرد «حالت دمو»
بک‌اند اجرا نیست. `python manage.py runserver` را اجرا کنید.

### `python: command not found` (ویندوز)
Python به PATH اضافه نشده. Python را دوباره نصب کنید با تیک `Add Python to PATH`.

### خطای `psycopg2`
از `requirements_local.txt` استفاده کنید (نیازی به PostgreSQL نیست).

### پورت اشغال
```bash
python manage.py runserver 8080    # بک‌اند روی پورت دیگر
npm run dev -- -p 3001              # فرانت‌اند روی پورت دیگر
```

### روی ویندوز، `manage.py` خطای مسیر می‌دهد
`manage.py` ریشه‌ی پروژه است. از همان پوشه اجرا کنید.

## ۸) ریست کامل پایگاه‌داده

```bash
cd workshop/backend
source venv/bin/activate
rm -f dev_test.db
python manage.py migrate
python manage.py seed_data
```

## ۹) تست نهایی

پس از نصب، این موارد را بررسی کنید:

- [ ] `http://localhost:8000/api/docs/` در مرورگر باز می‌شود (Swagger UI)
- [ ] `http://localhost:3000` صفحه‌ی ورود را نشان می‌دهد
- [ ] ورود با `admin` / `Admin@12345678` موفق است
- [ ] نوار «حالت دمو» نمی‌دهد (بک‌اند وصل است)
- [ ] ۹ بخش ناوبری همگی داده نشان می‌دهند:
  - [ ] داشبورد
  - [ ] محصولات (۱۰ محصول)
  - [ ] تولید
  - [ ] فروش (۸ فاکتور)
  - [ ] انبار
  - [ ] حسابداری
  - [ ] پخش و انتقال
  - [ ] گزارش‌ها (۷ تب با داده)
  - [ ] تنظیمات (۵ تب)
