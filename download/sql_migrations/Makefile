# ============================================================
# Makefile — اجرای ترتیبی Migrationها
# استفاده:
#   make init      # ساخت دیتابیس و اجرای همه فایل‌ها
#   make migrate   # فقط migrationها
#   make seed      # فقط داده‌های اولیه
#   make reset     # حذف و ساخت مجدد دیتابیس
#   make psql      # ورود به psql
#   make backup    # بکاپ دیتابیس
#   make restore   # بازگردانی از بکاپ
# ============================================================

# متغیرهای قابل تنظیم (از environment می‌تونن بازنویسی بشن)
DB_NAME ?= workshop_db
DB_USER ?= workshop_user
DB_PASSWORD ?= workshop_password
DB_HOST ?= localhost
DB_PORT ?= 5432
PSQL = PGPASSWORD=$(DB_PASSWORD) psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER)

# ترتیب اجرای فایل‌ها
MIGRATION_FILES = \
    001_create_extensions.sql \
    002_create_base_tables.sql \
    003_create_inventory_tables.sql \
    004_create_sales_tables.sql \
    005_create_accounting_tables.sql \
    006_create_mobile_portal_tables.sql \
    007_create_system_tables.sql \
    008_create_indexes.sql \
    009_create_triggers.sql

SEED_FILES = \
    010_seed_initial_data.sql

# ============================================================
# Targets اصلی
# ============================================================

.PHONY: init migrate seed reset psql backup restore help

help:
	@echo "Available targets:"
	@echo "  make init      - Create DB + run all migrations + seed"
	@echo "  make migrate   - Run all migration files (no seed)"
	@echo "  make seed      - Run only seed data"
	@echo "  make reset     - Drop and recreate database"
	@echo "  make psql      - Connect to database via psql"
	@echo "  make backup    - Create a backup of the database"
	@echo "  make restore  - Restore from latest backup"
	@echo "  make verify    - Run verification queries"
	@echo "  make help      - Show this help"

init: migrate seed
	@echo "✓ Database $(DB_NAME) initialized successfully"
	@echo "  Connect with: make psql"

migrate:
	@echo "→ Running migrations on database: $(DB_NAME)"
	@for file in $(MIGRATION_FILES); do \
	    echo "  → Running $$file..."; \
	    $(PSQL) -d $(DB_NAME) -1 -f $$file || exit 1; \
	done
	@echo "✓ All migrations completed"

seed:
	@echo "→ Seeding initial data..."
	@for file in $(SEED_FILES); do \
	    echo "  → Running $$file..."; \
	    $(PSQL) -d $(DB_NAME) -1 -f $$file || exit 1; \
	done
	@echo "✓ Seed data inserted"

reset:
	@echo "⚠ WARNING: This will DROP and recreate database $(DB_NAME)!"
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" != "yes" ]; then echo "Aborted."; exit 1; fi
	@echo "→ Dropping database $(DB_NAME)..."
	@$(PSQL) -d postgres -c "DROP DATABASE IF EXISTS $(DB_NAME);"
	@echo "→ Creating database $(DB_NAME)..."
	@$(PSQL) -d postgres -c "CREATE DATABASE $(DB_NAME) WITH OWNER $(DB_USER) ENCODING 'UTF8';"
	@$(MAKE) init
	@echo "✓ Database reset completed"

psql:
	@$(PSQL) -d $(DB_NAME)

backup:
	@echo "→ Creating backup..."
	@mkdir -p backups
	@PGPASSWORD=$(DB_PASSWORD) pg_dump -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) \
	    -d $(DB_NAME) -F c -f backups/$(DB_NAME)_$(shell date +%Y%m%d_%H%M%S).dump
	@echo "✓ Backup created in backups/"

restore:
	@LATEST=$$(ls -t backups/*.dump 2>/dev/null | head -1); \
	if [ -z "$$LATEST" ]; then echo "No backup found."; exit 1; fi; \
	echo "→ Restoring from: $$LATEST"; \
	PGPASSWORD=$(DB_PASSWORD) pg_restore -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) \
	    -d $(DB_NAME) -c $$LATEST; \
	echo "✓ Restore completed"

verify:
	@echo "→ Verifying database structure..."
	@$(PSQL) -d $(DB_NAME) -c "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
	@echo ""
	@$(PSQL) -d $(DB_NAME) -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
	@echo ""
	@$(PSQL) -d $(DB_NAME) -c "SELECT COUNT(*) AS users_count FROM users;"
	@$(PSQL) -d $(DB_NAME) -c "SELECT COUNT(*) AS products_count FROM products;"
	@$(PSQL) -d $(DB_NAME) -c "SELECT COUNT(*) AS stores_count FROM stores;"

# ============================================================
# Developer helpers
# ============================================================

.PHONY: test-data clean-test-data schema-diagram

test-data:
	@echo "→ Inserting test data for development..."
	@$(PSQL) -d $(DB_NAME) -1 -f tests/test_data.sql || echo "  (test_data.sql not found, skipping)"
	@echo "✓ Test data inserted"

clean-test-data:
	@echo "→ Cleaning test data..."
	@$(PSQL) -d $(DB_NAME) -c "TRUNCATE inventory_movements, inventory_lots, sales_lines, sales_headers CASCADE;"
	@$(PSQL) -d $(DB_NAME) -c "TRUNCATE journal_lines, journal_headers CASCADE;"
	@echo "✓ Test data cleaned (base data preserved)"

schema-diagram:
	@echo "→ Generating schema diagram..."
	@which postgresql_autodoc 2>/dev/null || echo "  Install: apt install postgresql-autodoc"
	@postgresql_autodoc -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) \
	    -d $(DB_NAME) -t html || echo "  (postgresql_autodoc not available)"

# ============================================================
# Docker helper (اگر از Docker Compose استفاده می‌شه)
# ============================================================

.PHONY: docker-up docker-down docker-logs

docker-up:
	@echo "→ Starting PostgreSQL via Docker..."
	@docker compose up -d postgres redis rabbitmq
	@echo "✓ Containers started"
	@echo "  Wait 10s for postgres to be ready..."
	@sleep 10
	@$(MAKE) init

docker-down:
	@echo "→ Stopping Docker containers..."
	@docker compose down
	@echo "✓ Containers stopped"

docker-logs:
	@docker compose logs -f postgres

# ============================================================
# Cleanup
# ============================================================

.PHONY: clean

clean:
	@rm -rf backups/*.dump
	@echo "✓ Old backups cleaned"
