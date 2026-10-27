#!/usr/bin/env bash
# ============================================================
# setup_complete.sh — نصب خودکار پروژه‌ی «نرم‌افزار جامع مدیریت تولید و پخش»
#
# این اسکریپت:
#   1. محیط مجازی Python می‌سازد و وابستگی‌های سبک بک‌اند را نصب می‌کند
#   2. مهاجرت‌های پایگاه‌داده را اعمال می‌کند
#   3. داده‌های اولیه (seed) را بارگذاری می‌کند
#   4. وابستگی‌های فرانت‌اند را نصب می‌کند
#   5. (اختیاری) بک‌اند و فرانت‌اند را اجرا می‌کند
#
# نحوه‌ی استفاده:
#   chmod +x setup_complete.sh
#   ./setup_complete.sh           # فقط نصب
#   ./setup_complete.sh --run     # نصب + اجرای هر دو سرور
#   ./setup_complete.sh --help
# ============================================================

set -euo pipefail

if [ -t 1 ] && command -v tput >/dev/null 2>&1; then
  GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1)
  BLUE=$(tput setaf 4); BOLD=$(tput bold); RESET=$(tput sgr0)
else
  GREEN="" YELLOW="" RED="" BLUE="" BOLD="" RESET=""
fi

log()  { echo "${GREEN}[✓]${RESET} $*"; }
warn() { echo "${YELLOW}[!]${RESET} $*"; }
err()  { echo "${RED}[✗]${RESET} $*" >&2; }
info() { echo "${BLUE}[i]${RESET} $*"; }
step() { echo ""; echo "${BOLD}${BLUE}━━━ $* ━━━${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RUN_AFTER=0
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<EOF
راهنما: setup_complete.sh
  بدون آرگومان      فقط نصب
  --run            نصب + اجرای هر دو سرور
  --help / -h       این راهنما
EOF
  exit 0
elif [ "${1:-}" = "--run" ]; then
  RUN_AFTER=1
fi

# تشخیص مسیرها
if [ -f "$SCRIPT_DIR/manage.py" ]; then
  BACKEND_DIR="$SCRIPT_DIR"
  for candidate in "$SCRIPT_DIR/../frontend" "$SCRIPT_DIR/../workshop_frontend" "$SCRIPT_DIR/frontend"; do
    if [ -d "$candidate" ] && [ -f "$candidate/package.json" ]; then
      FRONTEND_DIR="$candidate"; break
    fi
  done
  FRONTEND_DIR="${FRONTEND_DIR:-$SCRIPT_DIR/../frontend}"
elif [ -d "$SCRIPT_DIR/backend" ] && [ -f "$SCRIPT_DIR/backend/manage.py" ]; then
  BACKEND_DIR="$SCRIPT_DIR/backend"; FRONTEND_DIR="$SCRIPT_DIR/frontend"
elif [ -d "$SCRIPT_DIR/django_starter" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
  BACKEND_DIR="$SCRIPT_DIR/django_starter"; FRONTEND_DIR="$SCRIPT_DIR/frontend"
else
  err "نتوانستم ساختار پروژه را پیدا کنم."
  err "مسیر اسکریپت: $SCRIPT_DIR"
  exit 1
fi

BACKEND_DIR="$(cd "$BACKEND_DIR" && pwd)"
if [ -d "$FRONTEND_DIR" ]; then
  FRONTEND_DIR="$(cd "$FRONTEND_DIR" && pwd)"; FRONTEND_EXISTS=1
else
  FRONTEND_EXISTS=0
fi

echo "${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo "${BOLD}║  نصب «نرم‌افزار جامع مدیریت تولید و پخش»            ║${RESET}"
echo "${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo ""
info "بک‌اند:   $BACKEND_DIR"
info "فرانت‌اند: $([ $FRONTEND_EXISTS = 1 ] && echo "$FRONTEND_DIR" || echo "(پیدا نشد)")"
info "اجرا بعد از نصب: $([ $RUN_AFTER = 1 ] && echo "بله" || echo "خیر")"

if [ $FRONTEND_EXISTS = 0 ]; then
  warn "پوشه‌ی frontend پیدا نشد. فقط بک‌اند نصب می‌شود."
fi

# تشخیص Python — تلاش با py launcher ویندوز (ترجیح) و سپس python3/python
step "بررسی پیش‌نیازها"

# تابع کمکی: بررسی می‌کند یک باینری واقعاً قابل اجراست و نسخه برمی‌گرداند
try_python() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    if "$cmd" --version >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

PYTHON_BIN=""
# ترتیب اولویت: py launcher ویندوز با نسخه‌های 3.12/3.13/3.14، سپس python3، سپس python
for candidate in "py -3.12" "py -3.13" "py -3.14" python3 python; do
  if try_python $candidate; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  err "Python نصب نیست. از python.org دانلود کنید."
  err "روی ویندوز: py launcher را از python.org نصب کنید (پیشنهاد: Python 3.12+)."
  err "روی Linux/macOS: بسته‌ی python3 را از package manager خود نصب کنید."
  exit 1
fi
info "Python: $($PYTHON_BIN --version 2>&1)"

if ! command -v node >/dev/null 2>&1 && ! command -v bun >/dev/null 2>&1; then
  err "Node.js یا Bun نصب نیست. از nodejs.org یا bun.sh دانلود کنید."
  exit 1
fi
if command -v node >/dev/null 2>&1; then info "Node.js: $(node --version)"; fi
if command -v bun >/dev/null 2>&1; then info "Bun: $(bun --version)"; fi
log "پیش‌نیازها تأیید شد"

# نصب بک‌اند
step "نصب بک‌اند (Django)"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  info "ساخت محیط مجازی Python..."
  $PYTHON_BIN -m venv venv
fi
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  # shellcheck disable=SC1091
  source venv/Scripts/activate
else
  err "نتوانستم venv را فعال کنم."; exit 1
fi
info "Python در venv: $(python --version 2>&1)"

if [ -f "requirements_local.txt" ]; then
  REQ_FILE="requirements_local.txt"
  info "استفاده از $REQ_FILE (سبک، برای حالت محلی)"
else
  REQ_FILE="requirements.txt"; warn "استفاده از $REQ_FILE کامل (کندتر)"
fi
info "نصب وابستگی‌های Python (چند دقیقه)..."
python -m pip install --upgrade pip --quiet
python -m pip install -r "$REQ_FILE" --quiet
log "وابستگی‌های Python نصب شد"

if [ ! -f ".env" ]; then
  warn ".env وجود ندارد؛ ساختن نسخه‌ی محلی پیش‌فرض..."
  cat > .env <<'EOF'
SECRET_KEY=django-dev-test-key-change-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000
DATABASE_URL=sqlite:///dev_test.db
DJANGO_SETTINGS_MODULE=config.settings.local_test
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=django-db
REDIS_URL=redis://localhost:6379/0
EOF
  log ".env ساخته شد"
else
  if ! grep -q "DJANGO_SETTINGS_MODULE=config.settings.local_test" .env; then
    warn "DJANGO_SETTINGS_MODULE روی local_test تنظیم نیست. اضافه می‌کنم..."
    echo "DJANGO_SETTINGS_MODULE=config.settings.local_test" >> .env
  fi
fi

info "اعمال مهاجرت‌های پایگاه‌داده..."
python manage.py migrate --noinput
log "مهاجرت‌ها اعمال شد"

info "بارگذاری داده‌های اولیه (seed)..."
if python manage.py seed_data 2>&1 | tail -15; then
  log "داده‌های اولیه بارگذاری شد"
else
  warn "seed_data اخطار داد (شاید قبلاً اجرا شده)."
fi

info "بررسی Django (system check)..."
python manage.py check
log "بررسی Django موفق بود"

# نصب فرانت‌اند
if [ $FRONTEND_EXISTS = 1 ]; then
  step "نصب فرانت‌اند (Next.js)"
  cd "$FRONTEND_DIR"
  if command -v bun >/dev/null 2>&1; then
    info "استفاده از Bun (سریع‌تر)..."
    [ ! -d "node_modules" ] && bun install || info "node_modules موجود"
    PKG_MGR="bun"
  elif command -v npm >/dev/null 2>&1; then
    info "استفاده از npm..."
    [ ! -d "node_modules" ] && npm install || info "node_modules موجود"
    PKG_MGR="npm"
  else
    err "نه bun و نه npm."; exit 1
  fi
  log "وابستگی‌های $PKG_MGR نصب شد"
else
  PKG_MGR="npm"; warn "از نصب فرانت‌اند صرف‌نظر شد"
fi

# جمع‌بندی
step "نصب کامل شد! 🎉"
cat <<EOF

${GREEN}${BOLD}✅ نصب با موفقیت کامل شد.${RESET}

${BOLD}حساب‌های آماده:${RESET}
  admin           / Admin@12345678     (مدیر کل)
  accountant1     / Sample@12345678    (حسابدار)
  storekeeper1    / Sample@12345678    (انباردار)
  distributor1    / Sample@12345678    (عامل پخش)

${BOLD}برای اجرا:${RESET}

  # بک‌اند (ترمینال ۱):
  cd $BACKEND_DIR
  source venv/bin/activate        # روی ویندوز: venv\\Scripts\\activate
  python manage.py runserver

EOF

if [ $FRONTEND_EXISTS = 1 ]; then
  cat <<EOF
  # فرانت‌اند (ترمینال ۲):
  cd $FRONTEND_DIR
  $PKG_MGR run dev

EOF
fi

cat <<EOF
  # مرورگر: http://localhost:3000

${BOLD}راهنماها:${RESET}
  - نصب کامل:    $BACKEND_DIR/INSTALL_OTHER_PC.md
  - تست موبایل: $BACKEND_DIR/INSTALL_PHONE.md
  - چک‌لیست:     $BACKEND_DIR/TEST_CHECKLIST.md
EOF

if [ $RUN_AFTER = 1 ]; then
  if [ $FRONTEND_EXISTS = 0 ]; then warn "--run درخواست شد ولی frontend وجود ندارد."; fi
  step "اجرای سرورها (Ctrl+C برای توقف)"
  info "شروع بک‌اند روی پورت 8000..."
  cd "$BACKEND_DIR"
  source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
  python manage.py runserver 0.0.0.0:8000 &
  BACKEND_PID=$!
  info "بک‌اند PID: $BACKEND_PID"
  if [ $FRONTEND_EXISTS = 1 ]; then
    sleep 3
    info "شروع فرانت‌اند روی پورت 3000..."
    cd "$FRONTEND_DIR"
    if [ "$PKG_MGR" = "bun" ]; then bun run dev & else npm run dev & fi
    FRONTEND_PID=$!
    info "فرانت‌اند PID: $FRONTEND_PID"
    echo ""; info "هر دو سرور در حال اجرا هستند."
    info "  بک‌اند:   http://localhost:8000/api/docs/"
    info "  فرانت‌اند: http://localhost:3000"
  else
    echo ""; info "بک‌اند در حال اجرا است: http://localhost:8000/api/docs/"
  fi
  info "برای توقف، Ctrl+C را بزنید."
  trap "kill ${BACKEND_PID} ${FRONTEND_PID:-} 2>/dev/null; exit 0" INT TERM
  wait
fi

exit 0
