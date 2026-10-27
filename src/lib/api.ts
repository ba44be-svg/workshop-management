// API client for the Django REST backend on :8000.
//
// - Adds `Authorization: JWT <access>` header on every request.
// - On 401, tries to refresh the access token once; if refresh fails the
//   auth store is cleared and the user is bounced back to the login screen.
// - When the backend is unreachable (network error / Docker not running), the
//   client transparently falls back to a built-in mock layer so the UI stays
//   fully explorable. The flag is cached per-session.
//
// All request paths are relative to "/api/" — the backend root.

import { useAuthStore } from "@/store/auth-store";
import * as mock from "@/lib/mock-data";

function resolveBaseUrl(): string {
  if (typeof window === "undefined") return "http://localhost:8000/api";
  const host = window.location.hostname;
  return `http://${host}:8000/api`;
}
const BASE_URL = resolveBaseUrl();

let backendReachable: boolean | null = null;

// راجع‌شده با تاپIranibashim به‌خاطر اینکه نشانگر بصری "حالت دمو" را در UI نمایش دهیم.
// `null` = هنوز probes نشده (یا موفق بوده یا اولین بار).
// `false` = بک‌اند در دسترس نیست، mock فعال است.
// `true` = بک‌اند واقعی در دسترس است.
export function isDemoMode(): boolean {
  return backendReachable === false;
}

// subscription مکانیزم برای گوش دادن به تغییرات حالت demo
type Listener = (demo: boolean) => void;
const demoListeners: Set<Listener> = new Set();
export function subscribeDemoMode(listener: Listener): () => void {
  demoListeners.add(listener);
  return () => demoListeners.delete(listener);
}
function notifyDemoChange() {
  const demo = isDemoMode();
  demoListeners.forEach((l) => l(demo));
}

export function resetBackendProbe() {
  backendReachable = null;
  notifyDemoChange();
}

function getTokens() {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: window.localStorage.getItem("workshop_access"),
    refresh: window.localStorage.getItem("workshop_refresh"),
  };
}

function setTokens(access: string | null, refresh: string | null) {
  if (typeof window === "undefined") return;
  if (access) window.localStorage.setItem("workshop_access", access);
  else window.localStorage.removeItem("workshop_access");
  if (refresh) window.localStorage.setItem("workshop_refresh", refresh);
  else window.localStorage.removeItem("workshop_refresh");
}

export function clearTokens() {
  setTokens(null, null);
}

export interface Paginated<T> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
  next: string | null;
  previous: string | null;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function realFetch<T>(
  path: string,
  opts: RequestInit = {},
  attemptRefresh = true
): Promise<T> {
  const { access, refresh } = getTokens();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (access) headers["Authorization"] = `JWT ${access}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...opts, headers });

  if (res.status === 401 && attemptRefresh && refresh) {
    const ok = await tryRefresh();
    if (ok) return realFetch<T>(path, opts, false);
    // refresh failed — force logout
    useAuthStore.getState().logout();
    throw new ApiError(401, "نشست شما منقضی شد. لطفاً دوباره وارد شوید.");
  }

  if (!res.ok) {
    let detail: unknown = await res.text();
    try {
      detail = JSON.parse(detail as string);
    } catch {
      /* keep text */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

async function tryRefresh(): Promise<boolean> {
  const { refresh } = getTokens();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data.access) {
      setTokens(data.access, data.refresh ?? refresh);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Mock layer — mirrors the relevant endpoints for an offline demo.
// ---------------------------------------------------------------------------

interface MockCtx {
  method: string;
  body: unknown;
  query: Record<string, string>;
}

function paginate<T>(items: T[], query: Record<string, string>): Paginated<T> {
  const page = Math.max(1, parseInt(query.page ?? "1", 10));
  const pageSize = Math.max(1, parseInt(query.page_size ?? "20", 10));
  const start = (page - 1) * pageSize;
  const paged = items.slice(start, start + pageSize);
  return {
    count: items.length,
    page,
    page_size: pageSize,
    results: paged,
    next: start + pageSize < items.length ? "next" : null,
    previous: page > 1 ? "prev" : null,
  };
}

function mockRoute<T>(path: string, ctx: MockCtx): T | null {
  const { method, body, query } = ctx;
  const m = method.toUpperCase();
  const pathOnly = path.split("?")[0];

  // auth
  if (pathOnly === "/auth/login/" && m === "POST") {
    const b = body as { username?: string; password?: string };
    if (b.username === "admin" && b.password === "Admin@12345678") {
      return {
        access: "mock-access-token",
        refresh: "mock-refresh-token",
        user: mock.MOCK_USER,
      } as unknown as T;
    }
    throw new ApiError(401, "نام کاربری یا گذرواژه نادرست است.");
  }
  if (pathOnly === "/auth/me/" && m === "GET") return mock.MOCK_USER as unknown as T;
  if (pathOnly === "/auth/me/" && (m === "PATCH" || m === "PUT")) {
    const b = body as Record<string, unknown>;
    const updated = { ...mock.MOCK_USER, ...b };
    (mock as any).MOCK_USER = updated;
    return updated as unknown as T;
  }
  if (pathOnly === "/auth/logout/" && m === "POST") return undefined as unknown as T;

  // products — categories
  if (path.startsWith("/products/categories") && m === "GET")
    return mock.MOCK_CATEGORIES as unknown as T;

  // products
  if (pathOnly === "/products/" && m === "GET")
    return paginate(filterProducts(mock.MOCK_PRODUCTS, query), query) as unknown as T;
  if (pathOnly === "/products/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const unitId = Number(b.unit ?? 1);
    const unitObj = mock.MOCK_UNITS.find((u) => u.id === unitId);
    const next = {
      id: (mock.MOCK_PRODUCTS[0]?.id ?? 0) + 1,
      code: (b.code as string) ?? `P${(mock.MOCK_PRODUCTS[0]?.id ?? 0) + 1}`,
      name: (b.name as string) ?? "",
      barcode: (b.barcode as string) || `642${String(Date.now()).slice(-10)}`,
      default_price:
        typeof b.default_price === "string"
          ? b.default_price
          : Number(b.default_price ?? 0).toFixed(4),
      unit: unitId,
      unit_code: unitObj?.code ?? "NUM",
      unit_name: unitObj?.name ?? "عدد",
      is_finished_good: b.is_finished_good === true,
      is_active: b.is_active !== false,
      category: Number(b.category ?? 1),
      category_name:
        mock.MOCK_CATEGORIES.find((c) => c.id === Number(b.category ?? 1))
          ?.name ?? "—",
      shelf_life_days: Number(b.shelf_life_days ?? 3),
      description: (b.description as string) ?? "",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mock.MOCK_PRODUCTS.unshift(next);
    return next as unknown as T;
  }
  const productMatch = pathOnly.match(/^\/products\/(\d+)\/$/);
  if (productMatch) {
    const id = parseInt(productMatch[1], 10);
    if (m === "GET") {
      const p = mock.MOCK_PRODUCTS.find((x) => x.id === id);
      if (!p) throw new ApiError(404, "محصول یافت نشد.");
      return p as unknown as T;
    }
    if (m === "PUT" || m === "PATCH") {
      const b = body as Record<string, unknown>;
      const idx = mock.MOCK_PRODUCTS.findIndex((x) => x.id === id);
      if (idx === -1) throw new ApiError(404, "محصول یافت نشد.");
      mock.MOCK_PRODUCTS[idx] = { ...mock.MOCK_PRODUCTS[idx], ...b };
      return mock.MOCK_PRODUCTS[idx] as unknown as T;
    }
    if (m === "DELETE") {
      const idx = mock.MOCK_PRODUCTS.findIndex((x) => x.id === id);
      if (idx !== -1) mock.MOCK_PRODUCTS.splice(idx, 1);
      return undefined as unknown as T;
    }
  }

  // production
  if (pathOnly === "/production/batches/" && m === "GET")
    return paginate(mock.MOCK_BATCHES, query) as unknown as T;
  if (pathOnly === "/production/batches/create_batch/" && m === "POST") {
    const b = body as { product_id: number; planned_qty: string; notes?: string };
    const next = {
      id: mock.MOCK_BATCHES.length + 1,
      batch_no: `B-${240 + mock.MOCK_BATCHES.length + 1}`,
      product: mock.MOCK_PRODUCTS.find((p) => p.id === b.product_id),
      product_name: mock.MOCK_PRODUCTS.find((p) => p.id === b.product_id)?.name ?? "—",
      product_id: b.product_id,
      planned_qty: b.planned_qty,
      actual_qty: "0",
      waste_qty: "0",
      status: "planned",
      started_at: null,
      completed_at: null,
      created_at: new Date().toISOString(),
      notes: b.notes ?? "",
    };
    (mock.MOCK_BATCHES as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/production/batches/create/" && m === "POST") {
    const b = body as { product_id: number; planned_qty: string; notes?: string };
    const next = {
      id: mock.MOCK_BATCHES.length + 1,
      batch_no: `B-${240 + mock.MOCK_BATCHES.length + 1}`,
      product: mock.MOCK_PRODUCTS.find((p) => p.id === b.product_id),
      product_name: mock.MOCK_PRODUCTS.find((p) => p.id === b.product_id)?.name ?? "—",
      product_id: b.product_id,
      planned_qty: b.planned_qty,
      actual_qty: "0",
      waste_qty: "0",
      status: "planned",
      started_at: null,
      completed_at: null,
      created_at: new Date().toISOString(),
      notes: b.notes ?? "",
    };
    (mock.MOCK_BATCHES as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/production/batches/consume_material/" && m === "POST")
    return { ok: true } as unknown as T;
  if (pathOnly === "/production/batches/complete/" && m === "POST")
    return { ok: true } as unknown as T;
  if (pathOnly === "/production/outputs/create_output/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const batchId = Number(b.batch_id ?? 0);
    const batch = mock.MOCK_BATCHES.find((x) => x.id === batchId);
    const newId = (mock.MOCK_PRODUCTION_OUTPUTS[0]?.id ?? 0) + 1;
    const next = {
      id: newId,
      output_no: `OUT-2026-${String(newId).padStart(4, "0")}`,
      output_date: (b.output_date as string) ?? new Date().toISOString().slice(0, 10),
      batch: batchId,
      batch_no: batch?.batch_no ?? `B-${batchId}`,
      product: batch?.product_id ?? batch?.product?.id ?? null,
      product_name: (batch as any)?.product_name ?? batch?.product?.name ?? "—",
      warehouse: 4,
      warehouse_name: "انبار محصول تمام‌شده",
      total_qty: (b.lines as any[])?.reduce((s, l) => s + parseFloat(l.qty ?? "0"), 0) ?? 0,
      weighted_avg_cost: "15250.0000",
      total_value: "0.0000",
      status: "posted",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
      created_at: new Date().toISOString(),
      lines: Array.isArray(b.lines) ? b.lines : [],
    };
    (mock.MOCK_PRODUCTION_OUTPUTS as any[]).unshift(next);
    return next as unknown as T;
  }
  const batchDetailMatch = pathOnly.match(/^\/production\/batches\/(\d+)\/$/);
  if (batchDetailMatch && m === "GET") {
    const id = parseInt(batchDetailMatch[1], 10);
    const b = mock.MOCK_BATCHES.find((x) => x.id === id);
    if (!b) throw new ApiError(404, "بچ یافت نشد.");
    return b as unknown as T;
  }
  const batchMatch = pathOnly.match(/^\/production\/batches\/(\d+)\/(start|cancel)\/$/);
  if (batchMatch) {
    const id = parseInt(batchMatch[1], 10);
    const action = batchMatch[2];
    const idx = mock.MOCK_BATCHES.findIndex((x) => x.id === id);
    if (idx !== -1) {
      mock.MOCK_BATCHES[idx].status = action === "start" ? "in_progress" : "canceled";
      if (action === "start") mock.MOCK_BATCHES[idx].started_at = new Date().toISOString();
    }
    return mock.MOCK_BATCHES[idx] as unknown as T;
  }

  // inventory
  if (pathOnly === "/inventory/lots/" && m === "GET")
    return paginate(mock.MOCK_LOTS, query) as unknown as T;
  if (pathOnly === "/inventory/lots/near_expiry/" && m === "GET")
    return paginate(
      mock.MOCK_LOTS.filter((l) => {
        const days = Math.ceil((new Date(l.expiry_date).getTime() - Date.now()) / 86400000);
        return days >= 0;
      }),
      query
    ) as unknown as T;
  if (pathOnly === "/inventory/balances/" && m === "GET")
    return paginate(mock.MOCK_STOCK_BALANCE, query) as unknown as T;
  if (pathOnly === "/inventory/allocate-fefo/" && m === "POST")
    return {
      product_id: (body as { product_id: number }).product_id,
      allocated_qty: (body as { qty: string }).qty,
      lots: mock.MOCK_LOTS.slice(0, 2).map((l) => ({ lot_id: l.id, qty: l.qty_on_hand })),
    } as unknown as T;

  // sales
  if (pathOnly === "/sales/" && m === "GET")
    return paginate(mock.MOCK_SALES, query) as unknown as T;
  if (pathOnly === "/sales/create_sale/" && m === "POST") {
    const b = body as { store_id: number; sales_type: string; lines: Array<{ product_id: number; qty: string; unit_price: string }> };
    const lines = b.lines.map((l, j) => {
      const p = mock.MOCK_PRODUCTS.find((x) => x.id === l.product_id);
      const total = parseFloat(l.qty) * parseFloat(l.unit_price);
      return {
        id: (mock.MOCK_SALES.length + 1) * 10 + j,
        product: p,
        product_id: l.product_id,
        qty: l.qty,
        unit_price: l.unit_price,
        line_total: String(total),
      };
    });
    const total = lines.reduce((s, l) => s + parseFloat(l.line_total), 0);
    const next = {
      id: mock.MOCK_SALES.length + 1,
      sale_no: `S-${1400 + mock.MOCK_SALES.length + 1}`,
      store: mock.MOCK_STORES.find((s) => s.id === b.store_id),
      store_id: b.store_id,
      sales_type: b.sales_type,
      status: "draft",
      total_amount: String(total) + ".0000",
      total_cost: String(Math.round(total * 0.72)) + ".0000",
      total_profit: String(total - Math.round(total * 0.72)) + ".0000",
      created_at: new Date().toISOString(),
      lines,
    };
    (mock.MOCK_SALES as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/sales/daily_report/" && m === "GET")
    return mock.salesLast7Days() as unknown as T;
  const saleDetailMatch = pathOnly.match(/^\/sales\/(\d+)\/$/);
  if (saleDetailMatch && m === "GET") {
    const id = parseInt(saleDetailMatch[1], 10);
    const s = mock.MOCK_SALES.find((x) => x.id === id);
    if (!s) throw new ApiError(404, "فروش یافت نشد.");
    return s as unknown as T;
  }

  // partners
  if (pathOnly === "/partners/stores/" && m === "GET")
    return paginate(mock.MOCK_STORES, query) as unknown as T;
  if (pathOnly === "/partners/stores/geo_points/" && m === "GET")
    return { results: mock.MOCK_STORES } as unknown as T;
  if (path.startsWith("/partners/distributors") && m === "GET") {
    // Special: /partners/distributors/status/ — return mock status
    if (pathOnly === "/partners/distributors/status/") {
      const statuses = mock.MOCK_DISTRIBUTORS.map((d) => ({
        distributor_id: d.id,
        distributor_name: d.name,
        distributor_code: d.code,
        mobile: d.mobile,
        commission_rate: d.commission_rate,
        total_delivered_value: "0.0000",
        total_sold_value: "0.0000",
        total_returned_value: "0.0000",
        commission_owed: "0.0000",
        balance: "0.0000",
        store_count: Math.floor(Math.random() * 5) + 1,
        is_active: d.is_active,
      }));
      return { count: statuses.length, results: statuses } as unknown as T;
    }
    return paginate(mock.MOCK_DISTRIBUTORS, query) as unknown as T;
  }

  // wastes — mock endpoints
  if (pathOnly === "/inventory/wastes/" && m === "GET")
    return paginate(mock.MOCK_WASTES, query) as unknown as T;
  if (pathOnly === "/inventory/wastes/create_waste/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const newId = (mock.MOCK_WASTES[0]?.id ?? 0) + 1;
    const next = {
      id: newId,
      waste_no: `WST-2026-${String(newId).padStart(6, "0")}`,
      waste_type: (b.waste_type as string) ?? "warehouse",
      waste_type_display: ({ store: "فروشگاه", warehouse: "انبار", distributor: "عامل پخش" } as Record<string, string>)[(b.waste_type as string) ?? "warehouse"],
      store_name: b.waste_type === "store" ? mock.MOCK_STORES.find((s) => s.id === Number(b.store_id))?.name ?? "" : "",
      warehouse_name: b.waste_type === "warehouse" ? "انبار اصلی" : "",
      distributor_name: b.waste_type === "distributor" ? mock.MOCK_DISTRIBUTORS.find((d) => d.id === Number(b.distributor_id))?.name ?? "" : "",
      waste_date: new Date().toISOString().slice(0, 10),
      reason: (b.reason as string) ?? "",
      total_value: "0.0000",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
    };
    (mock.MOCK_WASTES as any[]).unshift(next);
    return next as unknown as T;
  }
  const storeBalanceMatch = pathOnly.match(/^\/partners\/stores\/(\d+)\/balance\/$/);
  if (storeBalanceMatch && m === "GET") {
    const id = parseInt(storeBalanceMatch[1], 10);
    const s = mock.MOCK_STORES.find((x) => x.id === id);
    return { store_id: id, balance: s?.balance ?? "0.0000" } as unknown as T;
  }

  // dispatch
  if (pathOnly === "/dispatch/" && m === "GET")
    return paginate(mock.MOCK_DISPATCHES, query) as unknown as T;
  if (pathOnly === "/dispatch/create_dispatch/" && m === "POST")
    return { id: mock.MOCK_DISPATCHES.length + 1, status: "draft", ...((body as object) ?? {}) } as unknown as T;

  // transfers
  if (pathOnly === "/transfers/" && m === "GET")
    return paginate(mock.MOCK_TRANSFERS, query) as unknown as T;
  if (pathOnly === "/transfers/create/" && m === "POST")
    return { id: mock.MOCK_TRANSFERS.length + 1, status: "pending", ...((body as object) ?? {}) } as unknown as T;
  const transferApproveMatch = pathOnly.match(/^\/transfers\/(\d+)\/approve\/$/);
  if (transferApproveMatch && m === "POST") {
    const id = parseInt(transferApproveMatch[1], 10);
    const idx = mock.MOCK_TRANSFERS.findIndex((x) => x.id === id);
    if (idx !== -1) mock.MOCK_TRANSFERS[idx].status = "approved";
    return mock.MOCK_TRANSFERS[idx] as unknown as T;
  }

  // accounting
  if (pathOnly === "/accounting/journals/" && m === "GET")
    return paginate(mock.MOCK_JOURNALS, query) as unknown as T;
  if (pathOnly === "/accounting/accounts/" && m === "GET")
    return { results: mock.MOCK_ACCOUNTS } as unknown as T;
  if (pathOnly === "/accounting/journals/create_manual/" && m === "POST") {
    const b = body as { date?: string; description?: string; lines?: Array<{ account_id: number; debit: string; credit: string }> };
    const total = (b.lines ?? []).reduce((s, l) => s + parseFloat(l.debit), 0);
    const next = {
      id: mock.MOCK_JOURNALS.length + 1,
      journal_no: `JV-${1400 + mock.MOCK_JOURNALS.length + 1}`,
      date: b.date ?? new Date().toISOString().slice(0, 10),
      description: b.description ?? "",
      total_debit: String(total) + ".0000",
      total_credit: String(total) + ".0000",
      status: "draft",
      lines: (b.lines ?? []).map((l, j) => ({
        id: (mock.MOCK_JOURNALS.length + 1) * 10 + j,
        account: mock.MOCK_ACCOUNTS.find((a) => a.id === l.account_id),
        debit: l.debit,
        credit: l.credit,
      })),
    };
    (mock.MOCK_JOURNALS as any[]).unshift(next);
    return next as unknown as T;
  }
  const journalDetailMatch = pathOnly.match(/^\/accounting\/journals\/(\d+)\/$/);
  if (journalDetailMatch && m === "GET") {
    const id = parseInt(journalDetailMatch[1], 10);
    const j = mock.MOCK_JOURNALS.find((x) => x.id === id);
    if (!j) throw new ApiError(404, "سند یافت نشد.");
    return j as unknown as T;
  }

  // workshop — contractors, purchases, issues, returns + warehouses
  if (pathOnly === "/workshop/contractors/" && m === "GET")
    return paginate(mock.MOCK_CONTRACTORS, query) as unknown as T;
  if (pathOnly === "/workshop/purchases/" && m === "GET")
    return paginate(mock.MOCK_PURCHASES, query) as unknown as T;
  const purchaseDetailMatch = pathOnly.match(/^\/workshop\/purchases\/(\d+)\/$/);
  if (purchaseDetailMatch && m === "GET") {
    const id = parseInt(purchaseDetailMatch[1], 10);
    const p = mock.MOCK_PURCHASES.find((x) => x.id === id);
    if (!p) throw new ApiError(404, "خرید یافت نشد.");
    return p as unknown as T;
  }
  if (pathOnly === "/workshop/purchases/create_purchase/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const newId = (mock.MOCK_PURCHASES[0]?.id ?? 0) + 1;
    const next = {
      id: newId,
      purchase_no: `PUR-2026-${String(newId).padStart(4, "0")}`,
      purchase_date: (b.purchase_date as string) ?? new Date().toISOString().slice(0, 10),
      contractor: Number(b.contractor ?? 1),
      contractor_name: mock.MOCK_CONTRACTORS.find((c) => c.id === Number(b.contractor ?? 1))?.name ?? "—",
      warehouse: Number(b.warehouse ?? 2),
      warehouse_name: mock.MOCK_WAREHOUSES.find((w) => w.id === Number(b.warehouse ?? 2))?.name ?? "—",
      cash_account: Number(b.cash_account ?? 1001),
      total_amount: "0.0000",
      total_qty: "0.00",
      notes: (b.notes as string) ?? "",
      journal: null,
      status: "posted",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
      created_at: new Date().toISOString(),
      lines: Array.isArray(b.lines) ? b.lines : [],
    };
    (mock.MOCK_PURCHASES as any[]).unshift(next);
    return next as unknown as T;
  }
  // ─── Purchase Returns ────────────────────────────────────────
  if (pathOnly === "/workshop/purchase-returns/" && m === "GET")
    return paginate(mock.MOCK_PURCHASE_RETURNS, query) as unknown as T;
  if (pathOnly === "/workshop/purchase-returns/create_return/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const newId = (mock.MOCK_PURCHASE_RETURNS[0]?.id ?? 0) + 1;
    const purchaseId = Number(b.purchase_id ?? 1);
    const purchase = mock.MOCK_PURCHASES.find((p) => p.id === purchaseId);
    const next = {
      id: newId,
      return_no: `PRT-2026-${String(newId).padStart(4, "0")}`,
      return_date: (b.return_date as string) ?? new Date().toISOString().slice(0, 10),
      purchase: purchaseId,
      purchase_no: purchase?.purchase_no ?? "PUR-???",
      contractor: purchase?.contractor ?? 1,
      contractor_name: purchase?.contractor_name ?? "—",
      warehouse: purchase?.warehouse ?? 2,
      warehouse_name: purchase?.warehouse_name ?? "—",
      cash_account: purchase?.cash_account ?? 1001,
      total_qty: "0.000",
      total_amount: "0.0000",
      reason: (b.reason as string) ?? "",
      journal: null,
      status: "posted",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
      created_at: new Date().toISOString(),
      lines: [],
    };
    (mock.MOCK_PURCHASE_RETURNS as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/workshop/issues/" && m === "GET")
    return paginate(mock.MOCK_WORKSHOP_ISSUES, query) as unknown as T;
  if (pathOnly === "/workshop/issues/create_issue/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const newId = (mock.MOCK_WORKSHOP_ISSUES[0]?.id ?? 0) + 1;
    const next = {
      id: newId,
      issue_no: `ISS-2026-${String(newId).padStart(4, "0")}`,
      issue_date: (b.issue_date as string) ?? new Date().toISOString().slice(0, 10),
      contractor: Number(b.contractor ?? 1),
      contractor_name: mock.MOCK_CONTRACTORS.find((c) => c.id === Number(b.contractor ?? 1))?.name ?? "—",
      from_warehouse: Number(b.from_warehouse ?? 2),
      to_warehouse: Number(b.to_warehouse ?? 5),
      production_batch: b.production_batch ?? null,
      total_qty: "0.00",
      total_value: "0.0000",
      notes: (b.notes as string) ?? "",
      journal: null,
      status: "posted",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
      created_at: new Date().toISOString(),
      lines: Array.isArray(b.lines) ? b.lines : [],
    };
    (mock.MOCK_WORKSHOP_ISSUES as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/workshop/returns/" && m === "GET")
    return paginate(mock.MOCK_WORKSHOP_RETURNS, query) as unknown as T;
  if (pathOnly === "/workshop/returns/create_return/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const newId = (mock.MOCK_WORKSHOP_RETURNS[0]?.id ?? 0) + 1;
    const next = {
      id: newId,
      return_no: `RET-2026-${String(newId).padStart(4, "0")}`,
      return_date: (b.return_date as string) ?? new Date().toISOString().slice(0, 10),
      issue: Number(b.issue ?? 0),
      contractor: Number(b.contractor ?? 1),
      contractor_name: mock.MOCK_CONTRACTORS.find((c) => c.id === Number(b.contractor ?? 1))?.name ?? "—",
      from_warehouse: Number(b.from_warehouse ?? 5),
      to_warehouse: Number(b.to_warehouse ?? 2),
      reason: (b.reason as string) ?? "",
      total_qty: "0.00",
      total_value: "0.0000",
      journal: null,
      status: "posted",
      lines_count: Array.isArray(b.lines) ? (b.lines as unknown[]).length : 0,
      created_at: new Date().toISOString(),
      lines: Array.isArray(b.lines) ? b.lines : [],
    };
    (mock.MOCK_WORKSHOP_RETURNS as any[]).unshift(next);
    return next as unknown as T;
  }
  // inventory/warehouses — CRUD with type filter
  if (pathOnly === "/inventory/warehouses/" && m === "GET") {
    let list = [...mock.MOCK_WAREHOUSES];
    if (query.type) list = list.filter((w) => w.type === query.type);
    if (query.is_active === "true") list = list.filter((w) => w.is_active === true);
    else if (query.is_active === "false") list = list.filter((w) => w.is_active === false);
    return paginate(list, query) as unknown as T;
  }
  if (pathOnly === "/inventory/warehouses/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const next = {
      id: (mock.MOCK_WAREHOUSES[0]?.id ?? 0) + 1,
      code: (b.code as string) ?? `WH-${Date.now()}`,
      name: (b.name as string) ?? "",
      type: (b.type as string) ?? "raw_materials",
      type_display: ({ main: "اصلی", raw_materials: "مواد اولیه",
                       finished_goods: "محصولات", workshop: "کارگاه",
                       store: "فروشگاه", virtual: "مجازی" } as Record<string, string>)[(b.type as string) ?? "raw_materials"],
      store: b.store ?? null,
      contractor: b.contractor ?? null,
      contractor_name: null,
      is_active: b.is_active !== false,
    };
    (mock.MOCK_WAREHOUSES as any[]).unshift(next);
    return next as unknown as T;
  }
  const whDetailMatch = pathOnly.match(/^\/inventory\/warehouses\/(\d+)\/$/);
  if (whDetailMatch) {
    const id = parseInt(whDetailMatch[1], 10);
    if (m === "PUT" || m === "PATCH") {
      const b = body as Record<string, unknown>;
      const idx = mock.MOCK_WAREHOUSES.findIndex((x) => x.id === id);
      if (idx === -1) throw new ApiError(404, "انبار یافت نشد.");
      mock.MOCK_WAREHOUSES[idx] = { ...mock.MOCK_WAREHOUSES[idx], ...b };
      return mock.MOCK_WAREHOUSES[idx] as unknown as T;
    }
    if (m === "DELETE") {
      const idx = mock.MOCK_WAREHOUSES.findIndex((x) => x.id === id);
      if (idx !== -1) mock.MOCK_WAREHOUSES.splice(idx, 1);
      return undefined as unknown as T;
    }
  }

  // products/units — list/create
  if (pathOnly === "/products/units/" && m === "GET")
    return paginate(mock.MOCK_UNITS, query) as unknown as T;
  if (pathOnly === "/products/units/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const next = {
      id: (mock.MOCK_UNITS[0]?.id ?? 0) + 1,
      code: (b.code as string) ?? "",
      name: (b.name as string) ?? "",
      is_active: b.is_active !== false,
      created_at: new Date().toISOString(),
    };
    (mock.MOCK_UNITS as any[]).unshift(next);
    return next as unknown as T;
  }
  const unitDetailMatch = pathOnly.match(/^\/products\/units\/(\d+)\/$/);
  if (unitDetailMatch) {
    const id = parseInt(unitDetailMatch[1], 10);
    if (m === "PUT" || m === "PATCH") {
      const b = body as Record<string, unknown>;
      const idx = mock.MOCK_UNITS.findIndex((x) => x.id === id);
      if (idx === -1) throw new ApiError(404, "واحد یافت نشد.");
      mock.MOCK_UNITS[idx] = { ...mock.MOCK_UNITS[idx], ...b };
      return mock.MOCK_UNITS[idx] as unknown as T;
    }
    if (m === "DELETE") {
      const idx = mock.MOCK_UNITS.findIndex((x) => x.id === id);
      if (idx !== -1) mock.MOCK_UNITS.splice(idx, 1);
      return undefined as unknown as T;
    }
  }

  // workshop/employees — list/create
  if (pathOnly === "/workshop/employees/" && m === "GET")
    return paginate(mock.MOCK_EMPLOYEES, query) as unknown as T;
  if (pathOnly === "/workshop/employees/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const first = (b.first_name as string) ?? "";
    const last = (b.last_name as string) ?? "";
    const next = {
      id: (mock.MOCK_EMPLOYEES[0]?.id ?? 0) + 1,
      code: (b.code as string) ?? `EMP-${Date.now()}`,
      first_name: first,
      last_name: last,
      full_name: `${first} ${last}`.trim(),
      national_id: (b.national_id as string) ?? "",
      mobile: (b.mobile as string) ?? "",
      phone: (b.phone as string) ?? "",
      position: (b.position as string) ?? "",
      workshop: b.workshop ?? null,
      workshop_name: "",
      hire_date: (b.hire_date as string) ?? new Date().toISOString().slice(0, 10),
      is_active: b.is_active !== false,
      created_at: new Date().toISOString(),
    };
    (mock.MOCK_EMPLOYEES as any[]).unshift(next);
    return next as unknown as T;
  }
  const empDetailMatch = pathOnly.match(/^\/workshop\/employees\/(\d+)\/$/);
  if (empDetailMatch) {
    const id = parseInt(empDetailMatch[1], 10);
    if (m === "PUT" || m === "PATCH") {
      const b = body as Record<string, unknown>;
      const idx = mock.MOCK_EMPLOYEES.findIndex((x) => x.id === id);
      if (idx === -1) throw new ApiError(404, "کارکنان یافت نشد.");
      const next = { ...mock.MOCK_EMPLOYEES[idx], ...b };
      if (next.first_name || next.last_name) {
        next.full_name = `${next.first_name ?? ""} ${next.last_name ?? ""}`.trim();
      }
      mock.MOCK_EMPLOYEES[idx] = next;
      return next as unknown as T;
    }
    if (m === "DELETE") {
      const idx = mock.MOCK_EMPLOYEES.findIndex((x) => x.id === id);
      if (idx !== -1) mock.MOCK_EMPLOYEES.splice(idx, 1);
      return undefined as unknown as T;
    }
  }

  // reports
  if (pathOnly === "/reports/store_receivables/" && m === "GET")
    return mock.MOCK_STORE_RECEIVABLES as unknown as T;
  if (pathOnly === "/reports/store_stock/" && m === "GET")
    return mock.MOCK_STORE_STOCK as unknown as T;
  if (pathOnly === "/reports/distributor_stock/" && m === "GET")
    return mock.MOCK_DISTRIBUTOR_STOCK as unknown as T;
  if (pathOnly === "/reports/distributor_commission/" && m === "GET")
    return mock.MOCK_DISTRIBUTOR_COMMISSION as unknown as T;
  if (pathOnly === "/reports/waste_report_detailed/" && m === "GET")
    return mock.MOCK_WASTE_DETAILED as unknown as T;
  if (pathOnly === "/reports/near_expiry/" && m === "GET")
    return mock.MOCK_NEAR_EXPIRY as unknown as T;
  if (pathOnly === "/reports/profit_report/" && m === "GET")
    return mock.MOCK_PROFIT as unknown as T;

  // auth management
  if (pathOnly === "/auth/users/" && m === "GET")
    return paginate(mock.MOCK_USERS, query) as unknown as T;
  if (pathOnly === "/auth/users/" && m === "POST") {
    const b = body as Record<string, unknown>;
    const next = {
      id: (mock.MOCK_USERS[0]?.id ?? 0) + 1,
      username: (b.username as string) ?? "",
      first_name: (b.first_name as string) ?? "",
      last_name: (b.last_name as string) ?? "",
      email: (b.email as string) ?? "",
      role: (b.role as string) ?? "viewer",
      is_active: b.is_active !== false,
    };
    (mock.MOCK_USERS as any[]).unshift(next);
    return next as unknown as T;
  }
  if (pathOnly === "/auth/company/" && (m === "GET" || m === "PATCH" || m === "PUT")) {
    if (m !== "GET") {
      const b = body as Record<string, unknown>;
      (mock as any).MOCK_COMPANY = { ...mock.MOCK_COMPANY, ...b };
    }
    return mock.MOCK_COMPANY as unknown as T;
  }
  if (pathOnly === "/auth/roles/" && m === "GET")
    return mock.MOCK_ROLES as unknown as T;

  return null;
}

function filterProducts<
  T extends {
    code?: string;
    name?: string;
    barcode?: string;
    is_active?: boolean;
    is_finished_good?: boolean;
  }
>(items: T[], query: Record<string, string>): T[] {
  let out = [...items];
  const search = query.search?.trim();
  if (search) {
    out = out.filter(
      (p) =>
        (p.code ?? "").toLowerCase().includes(search.toLowerCase()) ||
        (p.name ?? "").toLowerCase().includes(search.toLowerCase()) ||
        (p.barcode ?? "").includes(search)
    );
  }
  // /api/products/?is_active=true|false — فیلتر بک‌اند مبتنی بر bool
  const isActive = query.is_active;
  if (isActive === "true") out = out.filter((p) => p.is_active === true);
  else if (isActive === "false") out = out.filter((p) => p.is_active === false);
  // /api/products/?is_finished_good=false — فقط کالاهای خریداری (مواد اولیه)
  const isFinished = query.is_finished_good;
  if (isFinished === "true") out = out.filter((p) => p.is_finished_good === true);
  else if (isFinished === "false") out = out.filter((p) => p.is_finished_good === false);
  return out;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  rawBody?: boolean;
}

function buildPath(path: string, query?: Record<string, string | number | boolean | undefined>) {
  if (!query) return path;
  const params = Object.entries(query)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  if (!params) return path;
  return path.includes("?") ? `${path}&${params}` : `${path}?${params}`;
}

export async function api<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { body, query, rawBody, headers, ...rest } = opts;
  const fullPath = buildPath(path, query);
  const init: RequestInit = {
    ...rest,
    headers,
    body: body === undefined ? undefined : rawBody ? (body as BodyInit) : JSON.stringify(body),
  };
  const ctx: MockCtx = {
    method: rest.method ?? "GET",
    body: body,
    query: Object.fromEntries(
      Object.entries(query ?? {}).map(([k, v]) => [k, String(v ?? "")])
    ),
  };

  // If we already know the backend is down, use mock directly.
  if (backendReachable === false) {
    const mockRes = mockRoute<T>(fullPath, ctx);
    if (mockRes !== null) return mockRes;
    throw new ApiError(0, "بک‌اند در دسترس نیست و مسیر mock تعریف نشده است.");
  }

  try {
    const res = await realFetch<T>(fullPath, init);
    // اگر اولین درخواست موفق بود، بک‌اند را به‌عنوان قابل دسترس علامت بزن
    if (backendReachable !== true) {
      backendReachable = true;
      notifyDemoChange();
    }
    return res;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    // Network error → fall back to mock, mark backend as unreachable.
    backendReachable = false;
    notifyDemoChange();
    const mockRes = mockRoute<T>(fullPath, ctx);
    if (mockRes !== null) return mockRes;
    throw new ApiError(0, "بک‌اند در دسترس نیست.");
  }
}

// Auth helpers exposed to the store.
export { setTokens, getTokens };
