#!/bin/bash
# ============================================================
# اسکریپت راه‌اندازی پروژه با Docker
# راهنمای استفاده:
#   chmod +x deploy/docker/setup.sh
#   ./deploy/docker/setup.sh        # راه‌اندازی کامل
#   ./deploy/docker/setup.sh status  # فقط وضعیت
#   ./deploy/docker/setup.sh down     # توقف همه سرویس‌ها
#   ./deploy/docker/setup.sh logs     # دیدن لاگ‌ها
#   ./deploy/docker/setup.sh reset    # پاک‌سازی کامل (داده‌ها حذف می‌شوند!)
# ============================================================

set -e

# رنگ‌ها برای خروجی
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_ok() { echo -e "${GREEN}✓ $1${NC}"; }
print_info() { echo -e "${BLUE}→ $1${NC}"; }
print_warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_err() { echo -e "${RED}✗ $1${NC}"; }

# تغییر به دایرکتوری پروژه (root)
cd "$(dirname "$0")/../.."
PROJECT_ROOT="$(pwd)"

print_info "دایرکتوری پروژه: $PROJECT_ROOT"

# بررسی docker
if ! command -v docker &> /dev/null; then
    print_err "Docker نصب نیست!"
    echo "نصب:"
    echo "  ویندوز/مک: https://docker.com/products/docker-desktop"
    echo "  لینوکس (اوبونتو): sudo apt install docker.io docker-compose-plugin"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    print_err "Docker Compose v2 نصب نیست!"
    exit 1
fi

print_ok "Docker و Docker Compose آماده‌اند"

# بررسی فایل .env
if [ ! -f .env ]; then
    print_warn "فایل .env وجود ندارد. از .env.example کپی می‌کنیم..."
    cp .env.example .env
    print_ok ".env از .env.example ساخته شد"
    print_warn "لطفًا فایل .env را باز کرده و مقادیر حساس (SECRET_KEY, PASSWORDها) را تغییر دهید!"
fi

# ============================================================
# Action: status (وضعیت سرویس‌ها)
# ============================================================
if [ "$1" = "status" ]; then
    echo ""
    print_info "وضعیت سرویس‌های Docker:"
    docker compose ps
    echo ""
    print_info "آمار منابع:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker compose ps -q) 2>/dev/null || true
    exit 0
fi

# ============================================================
# Action: down (توقف)
# ============================================================
if [ "$1" = "down" ]; then
    print_info "توقف تمام سرویس‌ها..."
    docker compose down
    print_ok "همه سرویس‌ها متوقف شدند"
    exit 0
fi

# ============================================================
# Action: logs (لاگ‌ها)
# ============================================================
if [ "$1" = "logs" ]; then
    SERVICE="${2:-backend}"
    print_info "نمایش لاگ سرویس: $SERVICE (Ctrl+C برای خروج)"
    docker compose logs -f "$SERVICE"
    exit 0
fi

# ============================================================
# Action: reset (پاک‌سازی کامل)
# ============================================================
if [ "$1" = "reset" ]; then
    echo -n -e "${RED}این عمل تمام داده‌ها را (شامل دیتابیس) حذف می‌کند. آیا مطمئن هستی؟ [y/N] ${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "توقف و حذف همه containerها و volumeها..."
        docker compose down -v
        print_ok "پاک‌سازی کامل شد"
    else
        print_info "عمل لغو شد"
    fi
    exit 0
fi

# ============================================================
# Action: <default> — راه‌اندازی کامل
# ============================================================

print_info "شروع راه‌اندازی کامل پروژه..."

# مرحله ۱: Build images
print_info "مرحله ۱/۴: Build image‌ها..."
docker compose build --parallel
print_ok "Image‌ها ساخته شدند"

# مرحله ۲: Start infra services (Postgres, Redis, RabbitMQ)
print_info "مرحله ۲/۴: راه‌اندازی سرویس‌های زیرساختی (Postgres, Redis, RabbitMQ, MinIO)..."
docker compose up -d postgres redis rabbitmq minio

print_info "صبر برای آماده شدن سرویس‌های زیرساختی..."
timeout 90 bash -c '
while true; do
    if docker compose exec -T postgres pg_isready -U workshop_user 2>/dev/null | grep -q "accepting"; then
        echo -e "  Postgres آماده است"
        break
    fi
    sleep 2
done
'
timeout 30 bash -c 'until docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 2; done; echo "  Redis آماده است"'
timeout 30 bash -c 'until docker compose exec -T rabbitmq rabbitmq-diagnostics ping 2>/dev/null | grep -q "ok"; do sleep 2; done; echo "  RabbitMQ آماده است"'

print_ok "زیرساخت آماده است"

# مرحله ۳: Start backend
print_info "مرحله ۳/۴: راه‌اندازی Backend..."
docker compose up -d backend

print_info "صبر برای آماده شدن Backend (migrations اولیه)..."
timeout 120 bash -c '
while true; do
    if docker compose exec -T backend curl -sf http://localhost:8000/api/health/ 2>/dev/null | grep -q "ok"; then
        echo "  Backend آماده است"
        break
    fi
    sleep 3
done
'

print_ok "Backend در حال اجراست"

# مرحله ۴: Start Celery workers + Beat + Flower + Nginx
print_info "مرحله ۴/۴: راه‌اندازی Celery Worker, Beat, Flower و Nginx..."
docker compose up -d celery_worker celery_beat flower nginx
print_ok "تمام سرویس‌ها فعال شدند"

# مرحله ۵: Migrations + Seed + Superuser
echo ""
print_info "اجرای migrations و seed داده‌های اولیه..."
docker compose exec -T backend python manage.py migrate --noinput
print_ok "Migrations انجام شد"

docker compose exec -T backend python manage.py seed_data
print_ok "داده‌های seed شد"

# ساخت superuser اگر وجود ندارد
docker compose exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@workshop.local', 'Admin@12345678')
    print('  ✓ superuser ساخته شد: admin / Admin@12345678')
else:
    print('  • superuser از قبل وجود دارد')
"

# جمع‌بندی نهایی
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ پروژه با موفقیت راه‌اندازی شد!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  دسترسی‌ها:"
echo "  • Backend API:      http://localhost:8000/api/"
echo "  • Swagger UI:       http://localhost:8000/api/docs/"
echo "  • Django Admin:     http://localhost:8000/admin/"
echo "  • Flower (Celery):  http://localhost:5555/"
echo "  • MinIO Console:   http://localhost:9001/  (minio-access-key / minio-secret-key)"
echo "  • RabbitMQ Mgmt:    http://localhost:15672/  (guest / guest)"
echo ""
echo "  کاربر مدیر:"
echo "  • username: admin"
echo "  • password: Admin@12345678"
echo ""
echo "  برای دیدن وضعیت:      ./deploy/docker/setup.sh status"
echo "  برای دیدن لاگ‌ها:     ./deploy/docker/setup.sh logs backend"
echo "  برای توقف:           ./deploy/docker/setup.sh down"
echo "  برای پاک‌سازی کامل:  ./deploy/docker/setup.sh reset"
echo ""
