# 📱 راهنمای تست روی گوشی

> برنامه را روی گوشی یا تبلت از طریق شبکه‌ی Wi-Fi محلی تست کنید.

## ۱) پیدا کردن IP کامپیوتر

### ویندوز:
```powershell
ipconfig
```
خط `IPv4 Address` را پیدا کنید، مثلاً `192.168.1.100`.

### macOS / Linux:
```bash
# macOS:
ipconfig getifaddr en0

# Linux:
hostname -I
```

## ۲) اجرای بک‌اند با دسترسی از بیرون

```bash
cd workshop/backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

> حالت `local_test` تنظیم `CORS_ALLOW_ALL_ORIGINS=True` دارد، پس نیازی به تنظیم اضافی CORS نیست.

## ۳) اجرای فرانت‌اند با دسترسی از بیرون

```bash
cd workshop/frontend
npm run dev -- -H 0.0.0.0
```

خروجی باید نشان دهد:
```
- Network:      http://192.168.1.100:3000
```

> فایل `api.ts` به‌صورت پویا `window.location.hostname` را می‌گیرد، پس وقتی از گوشی به `http://192.168.1.100:3000` وصل می‌شوید، فرانت‌اند خودش به `http://192.168.1.100:8000/api` وصل می‌شود.

## ۴) تست روی گوشی

1. روی گوشی، مرورگر Chrome/Safari/Firefox باز کنید.
2. به `http://192.168.1.100:3000` بروید (IP کامپیوتر خود را جایگزین کنید).
3. وارد شوید: `admin` / `Admin@12345678`.
4. باید داشبورد نمایش داده شود و نوار «حالت دمو» نباشد.

## ۵) اشکال‌زدایی موبایل

### `ERR_CONNECTION_REFUSED`
- بک‌اند با `0.0.0.0:8000` اجرا نشده.
- فایروال ویندوز: Windows Security → Firewall → Allow an app → Node.js و Python را تیک بزنید (Private).

### نوار «حالت دمو»
بک‌اند از موبایل قابل دسترسی نیست. دلایل:
- بک‌اند روی `0.0.0.0:8000` اجرا نشده.
- فایروال پورت 8000 را مسدود می‌کند.
- گوشی و کامپیوتر روی Wi-Fi متفاوتی هستند.

### کندی
سرور توسعه‌ی Django برای موبایل بهینه نیست. برای تست نهایی:
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```
