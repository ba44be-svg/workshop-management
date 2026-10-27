# ✅ چک‌لیست تست

> پس از نصب کامل، این چک‌لیست را برای تأیید همه‌ی قابلیت‌ها اجرا کنید.

## ۱) بک‌اند (Django)

### سرور در حال اجراست
- [ ] `python manage.py runserver` خروجی «Starting development server at http://127.0.0.1:8000/» را می‌دهد.

### Health check
- [ ] `http://localhost:8000/api/health/` در مرورگر JSON با `"status": "ok"` برمی‌گرداند.

### Swagger UI
- [ ] `http://localhost:8000/api/docs/` صفحه‌ی Swagger UI را نمایش می‌دهد.

### ورود JWT
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@12345678"}'
```
- [ ] پاسخ شامل `"access"` و `"refresh"` است.

### گزارش‌های هفته‌ی ۵ (۷ endpoint)
```bash
TOKEN=<access از بالا>
curl "http://localhost:8000/api/reports/near_expiry/?days_threshold=7" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/store_receivables/?days=90" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/store_stock/?days=30" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/distributor_stock/?days=30" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/distributor_commission/?days=30" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/waste_report_detailed/?days=30" -H "Authorization: JWT $TOKEN"
curl "http://localhost:8000/api/reports/profit_report/?days=30&group_by=product" -H "Authorization: JWT $TOKEN"
```
- [ ] همه‌ی ۷ endpoint کد 200 برمی‌گردانند و داده دارند.

## ۲) فرانت‌اند (Next.js)

### سرور در حال اجراست
- [ ] `npm run dev` خروجی «Ready» را می‌دهد.

### صفحه‌ی ورود
- [ ] `http://localhost:3000` صفحه‌ی ورود را نمایش می‌دهد.
- [ ] عنوان پنل «پنل کارگاه تولید و پخش» است (نه «پنل مدیریت کارگاه نانوایی»).
- [ ] آیکون نان کراسان وجود ندارد — به‌جای آن آیکون عمومی (Factory) است.

### ورود
- [ ] ورود با `admin` / `Admin@12345678` موفق است.
- [ ] Toast «ورود موفقیت‌آمیز بود» نمایش داده می‌شود.
- [ ] به داشبورد منتقل می‌شوید.

### نوار دمو
- [ ] اگر بک‌اند در حال اجراست، نوار زرد «حالت دمو» نمی‌دهد.

### ناوبری (۹ بخش)
برای هر مورد کلیک کنید و مطمئن شوید صفحه باز می‌شود:

- [ ] **داشبورد** — کارت‌های آماری + جدول بچ‌های اخیر
- [ ] **محصولات** — ۱۰ محصول
- [ ] **تولید** — لیست بچ‌ها
- [ ] **فروش** — ۸ فاکتور فروش
- [ ] **انبار (FEFO)** — ۲ تب: موجودی + لات‌ها
- [ ] **حسابداری** — ژورنال‌ها + حساب‌ها
- [ ] **پخش و انتقال** — ۵ زیرتب
- [ ] **گزارش‌ها** — ۷ تب با داده
- [ ] **تنظیمات** — ۵ تب

### گزارش‌ها (۷ تب)
- [ ] **طلب از فروشگاه‌ها** — ۵ فروشگاه
- [ ] **کالای نزد فروشگاه** — ۵ ردیف
- [ ] **کالای نزد عامل پخش** — ۵ ردیف
- [ ] **دستمزد عوامل پخش** — ۳ عامل
- [ ] **گزارش ضایعات** — ۳ بخش
- [ ] **کالای نزدیک انقضا** — ۱۴ لات
- [ ] **گزارش سود** — ۸ محصول

### تنظیمات سیستم
- [ ] فیلد «عنوان پنل» قابل ویرایش است
- [ ] تغییر عنوان → سایدبار و فوتر فوراً آپدیت می‌شوند
- [ ] کلیک روی «جعبه‌ها» → آیکون سایدبار تغییر می‌کند

### تم تاریک
- [ ] دکمه‌ی ماه (☾) → رنگ‌ها تغییر می‌کنند

### واکنش‌گرا (موبایل)
- [ ] عرض 390px: منوی همبرگری (☰) ظاهر می‌شود
- [ ] فوتر در پایین چسبان است

## ۳) اشکال‌زدایی سریع

| علامت | علت | راه‌حل |
|---|---|---|
| صفحه سفید | خطای JavaScript | F12 → کنسول |
| نوار زرد دمو | بک‌اند اجرا نیست | `python manage.py runserver` |
| ورود خطا | بک‌اند در دسترس نیست | بک‌اند را اجرا کنید |
| داده‌ها خالی | seed اجرا نشده | `python manage.py seed_data` |
| ۴۰۴ در تولید | URL قدیمی | آخرین نسخه‌ی api.ts را نصب کنید |
