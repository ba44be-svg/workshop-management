# 🚀 راهنمای اجرای آنلاین برنامه

## روش ۱: Render.com (رایگان — پیشنهادی)

### قدم‌ها:
۱. به [render.com](https://render.com) برو و ثبت‌نام کن
۲. روی «New +» کلیک کن و «Blueprint» رو انتخاب کن
۳. پروژه‌ت رو به GitHub وصل کن (یا فایل‌ها رو آپلود کن)
۴. فایل `render.yaml` رو انتخاب کن
۵. Render خودش بک‌اند، فرانت‌اند و دیتابیس رو می‌سازه

### بعد از راه‌اندازی:
- بک‌اند: `https://workshop-backend.onrender.com`
- فرانت‌اند: `https://workshop-frontend.onrender.com`

---

## روش ۲: Railway.app (رایگان)

۱. به [railway.app](https://railway.app) برو
۲. «New Project» → «Deploy from GitHub repo»
۳. پروژه رو انتخاب کن
۴. Railway خودش Dockerfile رو پیدا می‌کنه و اجرا می‌کنه

---

## روش ۳: Vercel (فقط فرانت‌اند) + Render (بک‌اند)

### فرانت‌اند روی Vercel:
۱. به [vercel.com](https://vercel.com) برو
۲. پروژه رو import کن
۳. در تنظیمات، این env vars رو اضافه کن:
   - `NEXT_PUBLIC_API_URL` = `https://workshop-backend.onrender.com/api`

### بک‌اند روی Render:
همون روش ۱ بالا.

---

## روش ۴: سرویس ایرانی (پیشنهاد برای سرعت بیشتر)

### لیارا (Liara):
۱. به [liara.ir](https://liara.ir) برو
۲. پروژه‌ی Django ایجاد کن
۳. فایل‌های بک‌اند رو آپلود کن
۴. پروژه‌ی Node.js ایجاد کن
۵. فایل‌های فرانت‌اند رو آپلود کن

---

## 📝 نکات مهم

۱. **دیتابیس**: در محیط آنلاین از PostgreSQL استفاده می‌شود (نه SQLite)
۲. **Static files**: با `whitenoise` سرو می‌شوند
۳. **CORS**: همه‌ی origins مجاز هستند
۴. **ورود**: `admin` / `Admin@12345678` (بعد از migrate)

## 🎯 مزایای اجرای آنلاین

- ✅ از هر دستگاهی قابل دسترسی (موبایل، لپ‌تاپ)
- ✅ نیازی به نصب محلی نیست
- ✅ URL ثابت برای اشتراک‌گذاری
- ✅ همیشه در دسترس (24/7)
