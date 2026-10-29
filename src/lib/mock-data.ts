// Mock data layer — used as a fallback when the Django backend on :8000
// is unreachable. Shape mirrors DRF pagination (count/results/next/previous)
// and snake_case fields.

export const MOCK_USER = {
  id: 1,
  username: "admin",
  email: "admin@workshop.local",
  first_name: "مدیر",
  last_name: "کل",
  role: "manager",
  display_name: "مدیر کل",
};

const today = new Date();
const iso = (offsetDays = 0, h = 12, m = 0) => {
  const d = new Date(today);
  d.setDate(d.getDate() + offsetDays);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
};
const date = (offsetDays = 0) => iso(offsetDays).slice(0, 10);

export const MOCK_PRODUCTS = Array.from({ length: 23 }).map((_, i) => {
  const id = i + 1;
  const names = [
    "آرد سفید",
    "آرد سبوس‌دار",
    "شکر",
    "روغن مایع",
    "مخمر نانوایی",
    "نمک",
    "شیر خشک",
    "کره",
    "تخم مرغ",
    "وانیل",
    "نان بربری",
    "نان سنگک",
    "نان لواش",
    "کیک پادشاهی",
    "شیرمال",
    "کوکوی سبزی",
    "سوسیس بربری",
    "نان فانتزی",
    "بیسکویت کرمی",
    "کیک شکلاتی",
    "نان مغزدار",
    "باگت فرانسوی",
    "پیتزا فریز",
  ];
  // ۵ تای اول کالای خریداری (مواد اولیه)، بقیه محصول تمام‌شده
  const is_finished_good = i >= 5;
  const isActive = i % 9 !== 0; // هر ۹می غیرفعال
  const catId = is_finished_good ? 2 : 1; // 1=مواد اولیه، 2=محصول
  const catName = is_finished_good ? "محصول نهایی" : "مواد اولیه";
  return {
    id,
    code: `P${String(id).padStart(3, "0")}`,
    name: names[i] ?? `کالای ${id}`,
    barcode: `6200000${String(100000 + id).padStart(6, "0")}`,
    default_price: String(25000 + id * 3500) + ".0000",
    unit: 1,
    unit_code: "NUM",
    unit_name: "عدد",
    is_finished_good,
    is_active: isActive,
    category: catId,
    category_name: catName,
    shelf_life_days: 3 + (i % 10),
    description: "",
    created_at: iso(-30 - i),
    updated_at: iso(-30 - i),
  };
});

export const MOCK_CATEGORIES: Array<{
  id: number;
  code: string;
  name: string;
  parent: number | null;
  level: number;
  is_active: boolean;
  products_count: number;
}> = [
  { id: 1, code: "CAT-01", name: "نان سنتی", parent: null, level: 1, is_active: true, products_count: 12 },
  { id: 2, code: "CAT-02", name: "شیرینی",   parent: null, level: 1, is_active: true, products_count: 11 },
  { id: 3, code: "CAT-03", name: "کیک",       parent: 2,    level: 2, is_active: true, products_count: 5 },
  { id: 4, code: "CAT-04", name: "بیسکویت",   parent: 2,    level: 2, is_active: true, products_count: 4 },
];

export const MOCK_BATCHES = Array.from({ length: 14 }).map((_, i) => {
  const id = i + 1;
  const statuses = ["planned", "in_progress", "completed", "canceled"];
  const status = statuses[i % statuses.length];
  const planned = 50 + i * 20;
  const actual = status === "completed" ? planned - (i % 7) : status === "in_progress" ? Math.round(planned * 0.6) : 0;
  return {
    id,
    batch_no: `B-${String(240 + id)}`,
    product: MOCK_PRODUCTS[i % MOCK_PRODUCTS.length],
    product_id: MOCK_PRODUCTS[i % MOCK_PRODUCTS.length].id,
    planned_qty: String(planned),
    actual_qty: String(actual),
    waste_qty: status === "completed" ? String(i % 6) : "0",
    status,
    started_at: status === "planned" ? null : iso(-2 - i, 8),
    completed_at: status === "completed" ? iso(-1 - i, 16) : null,
    created_at: iso(-3 - i, 9),
    notes: `بچ ${status === "planned" ? "برنامه‌ریزی‌شده" : status === "in_progress" ? "در حال اجرا" : status === "completed" ? "تکمیل‌شده" : "لغوشده"}`,
  };
});

export const MOCK_SALES = Array.from({ length: 19 }).map((_, i) => {
  const id = i + 1;
  const linesCount = 1 + (i % 3);
  const lines = Array.from({ length: linesCount }).map((__, j) => {
    const qty = 5 + ((i + j) * 3) % 30;
    const price = String(30000 + ((i + j) * 2500)).slice(0, 5) + ".0000";
    return {
      id: id * 10 + j,
      product: MOCK_PRODUCTS[(i + j) % MOCK_PRODUCTS.length],
      product_id: MOCK_PRODUCTS[(i + j) % MOCK_PRODUCTS.length].id,
      qty: String(qty),
      unit_price: price,
      line_total: String(qty * parseFloat(price)),
    };
  });
  const total = lines.reduce((s, l) => s + parseFloat(l.line_total), 0);
  const cost = Math.round(total * 0.72);
  return {
    id,
    sale_no: `S-${String(1400 + id)}`,
    store: { id: (i % 8) + 1, name: `فروشگاه ${(i % 8) + 1}` },
    store_id: (i % 8) + 1,
    sales_type: i % 3 === 0 ? "consignment" : i % 3 === 1 ? "cash" : "credit",
    status: i % 5 === 0 ? "draft" : i % 5 === 1 ? "confirmed" : i % 5 === 2 ? "delivered" : i % 5 === 3 ? "invoiced" : "returned",
    total_amount: String(total) + ".0000",
    total_cost: String(cost) + ".0000",
    total_profit: String(total - cost) + ".0000",
    created_at: iso(-i, 10 + i),
    lines,
  };
});

export const MOCK_LOTS = Array.from({ length: 22 }).map((_, i) => {
  const id = i + 1;
  const expiryOffset = [-2, 1, 2, 5, 6, 8, 12, 18, 25, 40][i % 10];
  return {
    id,
    lot_no: `L-${String(900 + id)}`,
    product: MOCK_PRODUCTS[i % MOCK_PRODUCTS.length],
    product_id: MOCK_PRODUCTS[i % MOCK_PRODUCTS.length].id,
    warehouse: { id: (i % 3) + 1, name: `انبار ${(i % 3) + 1}` },
    warehouse_id: (i % 3) + 1,
    qty_on_hand: String(20 + i * 7),
    expiry_date: date(expiryOffset),
    received_at: iso(-10 - i, 9),
    status: expiryOffset < 0 ? "expired" : "available",
  };
});

export const MOCK_STOCK_BALANCE = MOCK_PRODUCTS.slice(0, 12).map((p, i) => ({
  product_id: p.id,
  product: { id: p.id, name: p.name, code: p.code },
  total_qty: String(40 + i * 12),
  warehouses: [
    { warehouse_id: 1, warehouse_name: "انبار ۱", qty: String(20 + i * 4) },
    { warehouse_id: 2, warehouse_name: "انبار ۲", qty: String(12 + i * 3) },
  ],
}));

export const MOCK_STORES = Array.from({ length: 8 }).map((_, i) => ({
  id: i + 1,
  code: `S${String(i + 1).padStart(3, "0")}`,
  name: `فروشگاه ${i + 1}`,
  owner: `صاحب فروشگاه ${i + 1}`,
  phone: `0912${String(1000000 + i).padStart(7, "0")}`,
  city: ["تهران", "کرج", "اصفهان", "شیراز", "مشهد", "تبریز", "اهواز", "رشت"][i],
  address: `تهران - محله ${i + 1}`,
  geo_lat: 35.6892 + (i - 4) * 0.05,
  geo_lng: 51.389 + (i - 4) * 0.04,
  distributor: 1,
  distributor_name: "عامل پخش مرکز",
  sales_model: "consignment",
  sales_model_display: "امانی",
  tier: ["regular", "silver", "gold", "platinum"][i % 4],
  tier_display: ["عادی", "نقره‌ای", "طلایی", "پلاتین"][i % 4],
  credit_limit: "500000000.0000",
  current_credit: String((i + 1) * 1000000) + ".0000",
  lat: 35.6892 + (i - 4) * 0.05,
  lng: 51.389 + (i - 4) * 0.04,
  balance: String((i + 1) * 1250000) + ".0000",
}));

export const MOCK_DISPATCHES = Array.from({ length: 9 }).map((_, i) => ({
  id: i + 1,
  dispatch_no: `D-${String(600 + i + 1)}`,
  store: MOCK_STORES[i % MOCK_STORES.length],
  store_id: MOCK_STORES[i % MOCK_STORES.length].id,
  driver: `راننده ${(i % 4) + 1}`,
  total_qty: String(120 + i * 15),
  status: i % 4 === 0 ? "draft" : i % 4 === 1 ? "loading" : i % 4 === 2 ? "in_transit" : "delivered",
  created_at: iso(-i, 7),
}));

export const MOCK_DISTRIBUTORS = Array.from({ length: 3 }).map((_, i) => ({
  id: i + 1,
  code: `D${String(i + 1).padStart(3, "0")}`,
  name: `عامل پخش ${["مرکز", "شمال", "جنوب"][i]}`,
  mobile: `0912${String(1000000 + i).padStart(7, "0")}`,
  commission_rate: String(5 + i),
  is_active: true,
}));

export const MOCK_WASTES = Array.from({ length: 5 }).map((_, i) => {
  const types = ["store", "warehouse", "distributor"];
  const wt = types[i % types.length];
  return {
    id: i + 1,
    waste_no: `WST-2026-${String(i + 1).padStart(6, "0")}`,
    waste_type: wt,
    waste_type_display: { store: "فروشگاه", warehouse: "انبار", distributor: "عامل پخش" }[wt],
    store_id: wt === "store" ? (i % 8) + 1 : null,
    store_name: wt === "store" ? MOCK_STORES[i % MOCK_STORES.length].name : "",
    warehouse_name: wt === "warehouse" ? "انبار اصلی" : "",
    distributor_id: wt === "distributor" ? (i % 3) + 1 : null,
    distributor_name: wt === "distributor" ? `عامل پخش ${["مرکز", "شمال", "جنوب"][i % 3]}` : "",
    waste_date: date(-i),
    reason: `دلیل ضایعات ${i + 1}`,
    total_value: String(50000 + i * 25000) + ".0000",
    lines_count: 1 + (i % 3),
  };
});

export const MOCK_TRANSFERS = Array.from({ length: 8 }).map((_, i) => ({
  id: i + 1,
  transfer_no: `T-${String(700 + i + 1)}`,
  from_store: MOCK_STORES[i % MOCK_STORES.length],
  from_store_id: MOCK_STORES[i % MOCK_STORES.length].id,
  from_store_name: MOCK_STORES[i % MOCK_STORES.length].name,
  to_store: MOCK_STORES[(i + 1) % MOCK_STORES.length],
  to_store_id: MOCK_STORES[(i + 1) % MOCK_STORES.length].id,
  to_store_name: MOCK_STORES[(i + 1) % MOCK_STORES.length].name,
  total_qty: String(40 + i * 8),
  status: i % 3 === 0 ? "pending" : i % 3 === 1 ? "approved" : "completed",
  created_at: iso(-i - 1, 8),
}));

export const MOCK_JOURNALS = Array.from({ length: 13 }).map((_, i) => {
  const id = i + 1;
  const total = 1200000 + i * 230000;
  return {
    id,
    journal_no: `JV-${String(1400 + id)}`,
    date: date(-i),
    description: `سند ${i % 2 === 0 ? "فروش" : "خرج تولید"} شماره ${id}`,
    total_debit: String(total) + ".0000",
    total_credit: String(total) + ".0000",
    status: i % 3 === 0 ? "draft" : i % 3 === 1 ? "posted" : "reversed",
    lines: [
      { id: id * 10 + 1, account: { id: 1001, code: "1001", name: "صندوق" }, debit: String(total), credit: "0.00" },
      { id: id * 10 + 2, account: { id: 4001, code: "4001", name: "فروش کالا" }, debit: "0.00", credit: String(total) },
    ],
  };
});

export const MOCK_ACCOUNTS = [
  { id: 1001, code: "1001", name: "صندوق", type: "asset", balance: "52400000.0000" },
  { id: 1002, code: "1002", name: "بانک ملت", type: "asset", balance: "320000000.0000" },
  { id: 1101, code: "1101", name: "موجودی کالا", type: "asset", balance: "184500000.0000" },
  { id: 1201, code: "1201", name: "حساب‌های دریافتنی", type: "asset", balance: "92300000.0000" },
  { id: 2001, code: "2001", name: "حساب‌های پرداختنی", type: "liability", balance: "64000000.0000" },
  { id: 4001, code: "4001", name: "فروش کالا", type: "revenue", balance: "0.0000" },
  { id: 5001, code: "5001", name: "بهای تمام‌شده کالای فروش‌رفته", type: "expense", balance: "0.0000" },
  { id: 5002, code: "5002", name: "دستمزد تولید", type: "expense", balance: "0.0000" },
  { id: 6001, code: "6001", name: "هزینه اداری", type: "expense", balance: "0.0000" },
];

// Dashboard helpers
export function dashboardKpis() {
  return {
    batches_today: MOCK_BATCHES.filter((b) => b.created_at.slice(0, 10) === date(0) || true).slice(0, 4).length,
    sales_today_rial: String(18400000) + ".0000",
    active_dispatches: MOCK_DISPATCHES.filter((d) => d.status !== "delivered").length,
    near_expiry_lots: MOCK_LOTS.filter((l) => {
      const days = Math.ceil((new Date(l.expiry_date).getTime() - Date.now()) / 86400000);
      return days >= 0 && days <= 7;
    }).length,
  };
}

export function salesLast7Days() {
  return Array.from({ length: 7 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return {
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      فروش: Math.round(12000000 + Math.random() * 9000000 + i * 400000),
    };
  });
}

export function productionLast7Days() {
  return Array.from({ length: 7 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return {
      date: `${d.getMonth() + 1}/${d.getDate()}`,
      تولید: Math.round(800 + Math.random() * 600 + i * 40),
      ضایعات: Math.round(20 + Math.random() * 60),
    };
  });
}

export function batchStatusBreakdown() {
  const counts: Record<string, number> = { planned: 0, in_progress: 0, completed: 0, canceled: 0 };
  for (const b of MOCK_BATCHES) counts[b.status]++;
  return [
    { name: "برنامه‌ریزی‌شده", value: counts.planned, key: "planned" },
    { name: "در حال اجرا", value: counts.in_progress, key: "in_progress" },
    { name: "تکمیل‌شده", value: counts.completed, key: "completed" },
    { name: "لغوشده", value: counts.canceled, key: "canceled" },
  ];
}

export function recentActivities() {
  return [
    { id: 1, type: "sale", title: "فروش جدید ثبت شد", subtitle: "S-1419 — فروشگاه ۳", at: iso(0, 9, 12) },
    { id: 2, type: "batch", title: "بچ تولید آغاز شد", subtitle: "B-244 — نان بربری", at: iso(0, 8, 30) },
    { id: 3, type: "dispatch", title: "سند پخش تحویل داده شد", subtitle: "D-605 — فروشگاه ۵", at: iso(-1, 18, 0) },
    { id: 4, type: "lot", title: "لات نزدیک انقضا", subtitle: "L-902 — نان سنگک", at: iso(-1, 14, 22) },
    { id: 5, type: "journal", title: "سند حسابداری ثبت شد", subtitle: "JV-1408", at: iso(-1, 11, 5) },
  ];
}

// ============================================================================
// گزارش‌ها و داده‌های مدیریت کاربران / شرکت / نقش‌ها
// ============================================================================

export const MOCK_STORE_RECEIVABLES = {
  period_days: 30,
  results: MOCK_STORES.slice(0, 5).map((s, i) => ({
    store_id: s.id,
    store_name: s.name,
    store_code: s.code,
    total_receivable: String(12_500_000 + i * 3_400_000) + ".0000",
    unsettled_count: 2 + (i % 4),
    sales: Array.from({ length: 2 + (i % 3) }).map((_, j) => ({
      sale_id: 1000 + i * 10 + j,
      sale_no: `S-${1400 + i * 10 + j}`,
      sale_date: date(-j - 1),
      amount: String(3_400_000 + j * 850_000) + ".0000",
    })),
  })),
};

export const MOCK_STORE_STOCK = {
  results: MOCK_STORES.slice(0, 4).flatMap((s, i) =>
    MOCK_PRODUCTS.slice(0, 3).map((p, j) => ({
      store_id: s.id,
      store_name: s.name,
      product_id: p.id,
      product_name: p.name,
      qty_on_hand: String(15 + i * 7 + j * 4),
      value: String((15 + i * 7 + j * 4) * parseFloat(p.default_price)) + ".0000",
    }))
  ),
  totals: {
    total_qty: String(MOCK_STORES.slice(0, 4).length * 3 * 28),
    total_value: String(MOCK_STORES.slice(0, 4).length * 3 * 28 * 35000) + ".0000",
  },
};

export const MOCK_DISTRIBUTOR_STOCK = {
  results: MOCK_DISTRIBUTORS.flatMap((d, i) =>
    MOCK_PRODUCTS.slice(0, 3).map((p, j) => ({
      distributor_id: d.id,
      distributor_name: d.name,
      product_id: p.id,
      product_name: p.name,
      qty_delivered: String(120 + i * 30 + j * 15),
      qty_returned: String((i + 1) * 4 + j),
      qty_on_hand: String(100 + i * 25 + j * 12),
      value: String((100 + i * 25 + j * 12) * parseFloat(p.default_price)) + ".0000",
    }))
  ),
};

export const MOCK_DISTRIBUTOR_COMMISSION = {
  period_days: 30,
  results: MOCK_DISTRIBUTORS.map((d, i) => {
    const delivered = 45_000_000 + i * 12_000_000;
    const sold = Math.round(delivered * 0.86);
    const returned = Math.round(delivered * 0.04);
    const rate = Number(d.commission_rate);
    const commission = Math.round(sold * rate / 100);
    return {
      distributor_id: d.id,
      distributor_name: d.name,
      commission_rate: d.commission_rate,
      total_delivered_value: String(delivered) + ".0000",
      total_sold_value: String(sold) + ".0000",
      total_returned_value: String(returned) + ".0000",
      commission_owed: String(commission) + ".0000",
    };
  }),
};

export const MOCK_WASTE_DETAILED = {
  period_days: 30,
  total_value: "1850000.0000",
  by_type: [
    { waste_type: "warehouse", waste_type_display: "انبار", total_value: "920000.0000", count: 4 },
    { waste_type: "store", waste_type_display: "فروشگاه", total_value: "640000.0000", count: 7 },
    { waste_type: "distributor", waste_type_display: "عامل پخش", total_value: "290000.0000", count: 3 },
  ],
  by_product: MOCK_PRODUCTS.slice(0, 4).map((p, i) => ({
    product_id: p.id,
    product_name: p.name,
    total_qty: String(8 + i * 3),
    total_value: String(120_000 + i * 65_000) + ".0000",
  })),
  details: Array.from({ length: 5 }).map((_, i) => {
    const wt = ["warehouse", "store", "distributor", "warehouse", "store"][i];
    const wd = { warehouse: "انبار", store: "فروشگاه", distributor: "عامل پخش" }[wt];
    return {
      waste_no: `WST-2026-${String(i + 1).padStart(6, "0")}`,
      waste_type: wt,
      waste_type_display: wd,
      location_name: wt === "store" ? MOCK_STORES[i % MOCK_STORES.length].name
        : wt === "distributor" ? MOCK_DISTRIBUTORS[i % MOCK_DISTRIBUTORS.length].name
        : "انبار اصلی",
      waste_date: date(-i - 1),
      total_value: String(85_000 + i * 38_000) + ".0000",
      lines_count: 1 + (i % 3),
    };
  }),
};

export const MOCK_NEAR_EXPIRY = {
  days_threshold: 7,
  today: date(0),
  count: MOCK_LOTS.filter((l) => {
    const days = Math.ceil((new Date(l.expiry_date).getTime() - Date.now()) / 86400000);
    return days >= 0 && days <= 14;
  }).length,
  results: MOCK_LOTS.filter((l) => {
    const days = Math.ceil((new Date(l.expiry_date).getTime() - Date.now()) / 86400000);
    return days >= 0 && days <= 14;
  }).map((l) => ({
    lot_id: l.id,
    lot_no: l.lot_no,
    product_id: l.product_id,
    product_name: l.product?.name ?? "—",
    expiry_date: l.expiry_date,
    days_remaining: Math.ceil((new Date(l.expiry_date).getTime() - Date.now()) / 86400000),
    qty_on_hand: l.qty_on_hand,
    warehouse_name: l.warehouse?.name ?? "انبار اصلی",
  })),
};

export const MOCK_PROFIT = {
  period_days: 30,
  group_by: "product",
  results: MOCK_PRODUCTS.slice(0, 6).map((p, i) => {
    const amount = 12_000_000 + i * 3_400_000;
    const cost = Math.round(amount * 0.72);
    const profit = amount - cost;
    return {
      key_id: p.id,
      key_name: p.name,
      total_amount: String(amount) + ".0000",
      total_cost: String(cost) + ".0000",
      total_profit: String(profit) + ".0000",
      margin_pct: Math.round((profit / amount) * 1000) / 10,
      sale_count: 12 + i * 3,
    };
  }),
  totals: {
    total_amount: String(MOCK_PRODUCTS.slice(0, 6).reduce((s, _, i) => s + 12_000_000 + i * 3_400_000, 0)) + ".0000",
    total_cost: String(MOCK_PRODUCTS.slice(0, 6).reduce((s, _, i) => s + Math.round((12_000_000 + i * 3_400_000) * 0.72), 0)) + ".0000",
    total_profit: String(MOCK_PRODUCTS.slice(0, 6).reduce((s, _, i) => {
      const a = 12_000_000 + i * 3_400_000;
      return s + (a - Math.round(a * 0.72));
    }, 0)) + ".0000",
    margin_pct: 28,
  },
};

export const MOCK_USERS = [
  { id: 1, username: "admin", first_name: "مدیر", last_name: "کل", email: "admin@workshop.local", role: "admin", is_active: true },
  { id: 2, username: "accountant1", first_name: "حسابدار", last_name: "اول", email: "accountant@workshop.local", role: "accountant", is_active: true },
  { id: 3, username: "storekeeper1", first_name: "انباردار", last_name: "اصلی", email: "keeper@workshop.local", role: "storekeeper", is_active: true },
  { id: 4, username: "distributor1", first_name: "عامل", last_name: "پخش مرکز", email: "dist1@workshop.local", role: "distributor", is_active: true },
  { id: 5, username: "sales1", first_name: "فروشنده", last_name: "پشتیبان", email: "sales@workshop.local", role: "sales", is_active: true },
  { id: 6, username: "viewer1", first_name: "بیننده", last_name: "سیستم", email: "viewer@workshop.local", role: "viewer", is_active: false },
];

export const MOCK_COMPANY = {
  name: "کارگاه نانوایی و شیرینی‌پزی پارس",
  legal_name: "شرکت تولید و توزیع فرآورده‌های غذایی پارس (سهامی خاص)",
  tax_id: "14008812345",
  economic_code: "411223456789",
  phone: "021-88123456",
  address: "تهران - خیابان ولیعصر - بالاتر از میدان ونک - پلاک ۲۴۵",
  city: "تهران",
};

export const MOCK_ROLES = [
  {
    key: "admin",
    name: "مدیر سیستم",
    description: "دسترسی کامل به همه بخش‌ها",
    permissions: ["dashboard", "products", "production", "sales", "inventory", "accounting", "dispatch", "reports", "settings"],
  },
  {
    key: "accountant",
    name: "حسابدار",
    description: "دسترسی به حسابداری و گزارش‌ها",
    permissions: ["dashboard", "accounting", "reports"],
  },
  {
    key: "storekeeper",
    name: "انباردار",
    description: "مدیریت انبار و لات‌ها",
    permissions: ["dashboard", "inventory", "products"],
  },
  {
    key: "distributor",
    name: "عامل پخش",
    description: "مشاهده سندهای پخش و موجودی",
    permissions: ["dashboard", "dispatch"],
  },
];

// ============================================================================
// Workshop module — Contractors, Purchases, Issues, Returns, Warehouses
// ============================================================================

export const MOCK_CONTRACTORS = [
  {
    id: 1,
    code: "C001",
    name: "کارپرداز محسن رضایی",
    national_id: "0012345678",
    mobile: "09121001001",
    phone: "021-88100001",
    address: "تهران - خیابان ولیعصر - پلاک ۱۰",
    workshop_name: "بربری محسن",
    is_active: true,
    detail_account: { id: 1401, code: "140/C001", name: "بدهکاران کارگاه: بربری محسن" },
  },
  {
    id: 2,
    code: "C002",
    name: "کارپرداز گلستان احمدی",
    national_id: "0023456789",
    mobile: "09121002002",
    phone: "021-88200002",
    address: "تهران - خیابان آزادی - پلاک ۲۰",
    workshop_name: "شیرینی گلستان",
    is_active: true,
    detail_account: { id: 1402, code: "140/C002", name: "بدهکاران کارگاه: شیرینی گلستان" },
  },
  {
    id: 3,
    code: "C003",
    name: "کارگاه کیک پارس",
    national_id: "0034567890",
    mobile: "09121003003",
    phone: "021-88300003",
    address: "تهران - خیابان انقلاب - پلاک ۳۰",
    workshop_name: "کیک پارس",
    is_active: false,
    detail_account: { id: 1403, code: "140/C003", name: "بدهکاران کارگاه: کیک پارس" },
  },
];

export const MOCK_WAREHOUSES = [
  { id: 1, code: "WH-MAIN", name: "انبار اصلی مرکز", type: "main", type_display: "اصلی", store: null, contractor: null, contractor_name: null, is_active: true },
  { id: 2, code: "WH-RAW-1", name: "انبار مواد اولیه آرد", type: "raw_materials", type_display: "مواد اولیه", store: null, contractor: null, contractor_name: null, is_active: true },
  { id: 3, code: "WH-RAW-2", name: "انبار مواد اولیه شکر/روغن", type: "raw_materials", type_display: "مواد اولیه", store: null, contractor: null, contractor_name: null, is_active: true },
  { id: 4, code: "WH-FG", name: "انبار محصول تمام‌شده", type: "finished_goods", type_display: "محصول تمام‌شده", store: null, contractor: null, contractor_name: null, is_active: true },
  { id: 5, code: "WS-C001", name: "کارگاه بربری محسن", type: "workshop", type_display: "کارگاه", store: null, contractor: 1, contractor_name: "کارپرداز محسن رضایی", is_active: true },
  { id: 6, code: "WS-C002", name: "کارگاه شیرینی گلستان", type: "workshop", type_display: "کارگاه", store: null, contractor: 2, contractor_name: "کارپرداز گلستان احمدی", is_active: true },
  { id: 7, code: "WS-C003", name: "کارگاه کیک پارس", type: "workshop", type_display: "کارگاه", store: null, contractor: 3, contractor_name: "کارپرداز کیک پارس", is_active: true },
];

export const MOCK_PURCHASES = [
  {
    id: 1,
    purchase_no: "PUR-2026-0001",
    purchase_date: date(-1),
    contractor: 1,
    contractor_name: "کارپرداز محسن رضایی",
    warehouse: 2,
    warehouse_name: "انبار مواد اولیه آرد",
    cash_account: 1001,
    total_amount: "4250000.0000",
    total_qty: "200.00",
    notes: "خرید آرد فله‌ای",
    journal: { id: 9001, journal_no: "JV-9001", date: date(-1) },
    status: "posted",
    lines_count: 2,
    created_at: iso(-1, 9),
    lines: [
      { id: 11, product: 1, product_name: "آرد سبوس‌دار", qty: "150", unit_price: "18000", shelf_life_days: 60, expiry_date: date(59), lot_no: "PUR-1-1", line_total: "2700000.0000" },
      { id: 12, product: 2, product_name: "آرد سفید", qty: "50", unit_price: "31000", shelf_life_days: 45, expiry_date: date(44), lot_no: "PUR-1-2", line_total: "1550000.0000" },
    ],
  },
  {
    id: 2,
    purchase_no: "PUR-2026-0002",
    purchase_date: date(0),
    contractor: 2,
    contractor_name: "کارپرداز گلستان احمدی",
    warehouse: 3,
    warehouse_name: "انبار مواد اولیه شکر/روغن",
    cash_account: 1002,
    total_amount: "8750000.0000",
    total_qty: "350.00",
    notes: "خرید شکر و روغن",
    journal: null,
    status: "draft",
    lines_count: 2,
    created_at: iso(0, 10),
    lines: [
      { id: 21, product: 3, product_name: "شکر سفید", qty: "200", unit_price: "28000", shelf_life_days: 180, expiry_date: date(179), lot_no: "PUR-2-1", line_total: "5600000.0000" },
      { id: 22, product: 4, product_name: "روغن مایع", qty: "150", unit_price: "21000", shelf_life_days: 120, expiry_date: date(119), lot_no: "PUR-2-2", line_total: "3150000.0000" },
    ],
  },
];

export const MOCK_PURCHASE_RETURNS = [
  {
    id: 1,
    return_no: "PRT-2026-0001",
    return_date: date(-1),
    purchase: 1,
    purchase_no: "PUR-2026-0001",
    contractor: 1,
    contractor_name: "کارپرداز محسن رضایی",
    warehouse: 2,
    warehouse_name: "انبار مواد اولیه آرد",
    cash_account: 1001,
    total_qty: "20.000",
    total_amount: "360000.0000",
    reason: "کیفیت نامناسب",
    journal: { id: 9002, journal_no: "JV-9002", date: date(-1) },
    status: "posted",
    lines_count: 1,
    created_at: iso(-1, 14),
    lines: [
      { id: 21, purchase_line: 11, product: 1, product_name: "آرد سبوس‌دار", lot: 5, lot_no: "PUR-1-1", qty: "20", unit_price: "18000", line_total: "360000.0000" },
    ],
  },
];

export const MOCK_WORKSHOP_ISSUES = [
  {
    id: 1,
    issue_no: "ISS-2026-0001",
    issue_date: date(0),
    contractor: 1,
    contractor_name: "کارپرداز محسن رضایی",
    from_warehouse: 2,
    to_warehouse: 5,
    production_batch: null,
    total_qty: "100.00",
    total_value: "1800000.0000",
    notes: "حواله آرد برای بچ صبح",
    journal: { id: 9002, journal_no: "JV-9002", date: date(0) },
    status: "posted",
    lines_count: 1,
    created_at: iso(0, 7),
    lines: [
      { id: 101, product: 1, product_name: "آرد سبوس‌دار", lot: 5, lot_no: "PUR-1-1", qty: "100", unit_cost: "18000", line_total: "1800000.0000" },
    ],
  },
  {
    id: 2,
    issue_no: "ISS-2026-0002",
    issue_date: date(-1),
    contractor: 2,
    contractor_name: "کارپرداز گلستان احمدی",
    from_warehouse: 3,
    to_warehouse: 6,
    production_batch: 3,
    total_qty: "80.00",
    total_value: "2240000.0000",
    notes: "مواد اولیه کیک",
    journal: { id: 9003, journal_no: "JV-9003", date: date(-1) },
    status: "posted",
    lines_count: 2,
    created_at: iso(-1, 8),
    lines: [
      { id: 102, product: 3, product_name: "شکر سفید", lot: 6, lot_no: "PUR-2-1", qty: "50", unit_cost: "28000", line_total: "1400000.0000" },
      { id: 103, product: 4, product_name: "روغن مایع", lot: 6, lot_no: "PUR-2-2", qty: "40", unit_cost: "21000", line_total: "840000.0000" },
    ],
  },
];

export const MOCK_WORKSHOP_RETURNS = [
  {
    id: 1,
    return_no: "RET-2026-0001",
    return_date: date(0),
    issue: 1,
    contractor: 1,
    contractor_name: "کارپرداز محسن رضایی",
    from_warehouse: 5,
    to_warehouse: 2,
    reason: "مقدار اضافی تحویلی",
    total_qty: "20.00",
    total_value: "360000.0000",
    journal: { id: 9004, journal_no: "JV-9004", date: date(0) },
    status: "posted",
    lines_count: 1,
    created_at: iso(0, 14),
    lines: [
      { id: 201, issue_line: 101, product: 1, product_name: "آرد سبوس‌دار", lot_no: "PUR-1-1", qty: "20", unit_cost: "18000", line_total: "360000.0000" },
    ],
  },
];

export const MOCK_UNITS = [
  { id: 1, code: "NUM",  name: "عدد",    is_active: true, created_at: iso(-30) },
  { id: 2, code: "KG",   name: "کیلوگرم", is_active: true, created_at: iso(-30) },
  { id: 3, code: "G",    name: "گرم",     is_active: true, created_at: iso(-30) },
  { id: 4, code: "L",    name: "لیتر",    is_active: true, created_at: iso(-30) },
  { id: 5, code: "PACK", name: "بسته",   is_active: true, created_at: iso(-30) },
  { id: 6, code: "BOX",  name: "جعبه",   is_active: true, created_at: iso(-30) },
  { id: 7, code: "M",    name: "متر",    is_active: true, created_at: iso(-30) },
  { id: 8, code: "M2",   name: "متر مربع", is_active: true, created_at: iso(-30) },
];

export const MOCK_EMPLOYEES = [
  { id: 1, code: "EMP-001", first_name: "رضا",   last_name: "محمدی",  full_name: "رضا محمدی",
    national_id: "0011111111", mobile: "09123330011", phone: "",
    position: "مسئول کارگاه", workshop: 5, workshop_name: "کارگاه رضایی",
    hire_date: date(-365), is_active: true, created_at: iso(-365) },
  { id: 2, code: "EMP-002", first_name: "محمد",  last_name: "حسینی",  full_name: "محمد حسینی",
    national_id: "0022222222", mobile: "09123330012", phone: "",
    position: "انباردار کارگاه", workshop: 5, workshop_name: "کارگاه رضایی",
    hire_date: date(-300), is_active: true, created_at: iso(-300) },
  { id: 3, code: "EMP-003", first_name: "فاطمه", last_name: "رضایی",  full_name: "فاطمه رضایی",
    national_id: "0033333333", mobile: "09123330013", phone: "",
    position: "کارگر تولید", workshop: 6, workshop_name: "کارگاه موسوی",
    hire_date: date(-250), is_active: true, created_at: iso(-250) },
  { id: 4, code: "EMP-004", first_name: "علی",   last_name: "اکبری",  full_name: "علی اکبری",
    national_id: "0044444444", mobile: "09123330014", phone: "",
    position: "کارگر تولید", workshop: 6, workshop_name: "کارگاه موسوی",
    hire_date: date(-200), is_active: true, created_at: iso(-200) },
  { id: 5, code: "EMP-005", first_name: "زهرا",  last_name: "کریمی",  full_name: "زهرا کریمی",
    national_id: "0055555555", mobile: "09123330015", phone: "",
    position: "مسئول کارگاه", workshop: 1, workshop_name: "انبار اصلی مرکز",
    hire_date: date(-150), is_active: true, created_at: iso(-150) },
];

export const MOCK_PRODUCTION_OUTPUTS = [
  {
    id: 1,
    output_no: "OUT-2026-0001",
    output_date: date(0),
    batch: 3,
    batch_no: "B-243",
    product: 1,
    product_name: "نان بربری",
    warehouse: 4,
    warehouse_name: "انبار محصول تمام‌شده",
    total_qty: "180.00",
    weighted_avg_cost: "15250.0000",
    total_value: "2745000.0000",
    status: "posted",
    lines_count: 1,
    created_at: iso(0, 16),
    lines: [
      { id: 301, lot_no: "FG-B-243-1", qty: "180", expiry_date: date(2), unit_cost: "15250", line_total: "2745000.0000" },
    ],
  },
];

// ============================================================================
// D02 — تحویل به عوامل پخش: داده‌های موک برای ۴ گزارش + settlement_check
// ============================================================================

export const MOCK_DISTRIBUTION_REPORTS = {
  settlement_check: {
    distributor_id: 1,
    has_unsettled: true,
    unsettled_count: 2,
    warning: "این عامل پخش تحویل تسویه‌نشده دارد. لطفاً ابتدا تسویه کنید.",
  },
  summary: {
    start_date: date(-30),
    end_date: date(0),
    results: MOCK_DISTRIBUTORS.map((d, i) => {
      const delivered = 45_000_000 + i * 12_000_000;
      const sold = Math.round(delivered * 0.78);
      const toStores = Math.round(delivered * 0.82);
      const returned = Math.round(delivered * 0.04);
      const balance = delivered - sold - returned;
      const rate = Number(d.commission_rate);
      return {
        distributor_id: d.id,
        distributor_code: d.code,
        distributor_name: d.name,
        total_delivered_value: String(delivered) + ".0000",
        total_sold_value: String(sold) + ".0000",
        total_to_stores_value: String(toStores) + ".0000",
        total_returned_value: String(returned) + ".0000",
        balance: String(balance) + ".0000",
        commission_rate: d.commission_rate,
        commission_owed: String(Math.round(sold * rate / 100)) + ".0000",
        store_count: 3 + (i % 4),
      };
    }),
    totals: {
      total_delivered_value: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => s + 45_000_000 + i * 12_000_000, 0)) + ".0000",
      total_sold_value: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => s + Math.round((45_000_000 + i * 12_000_000) * 0.78), 0)) + ".0000",
      total_to_stores_value: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => s + Math.round((45_000_000 + i * 12_000_000) * 0.82), 0)) + ".0000",
      total_returned_value: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => s + Math.round((45_000_000 + i * 12_000_000) * 0.04), 0)) + ".0000",
      balance: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => {
        const del = 45_000_000 + i * 12_000_000;
        return s + (del - Math.round(del * 0.78) - Math.round(del * 0.04));
      }, 0)) + ".0000",
      commission_owed: String(MOCK_DISTRIBUTORS.reduce((s, d, i) => {
        const del = 45_000_000 + i * 12_000_000;
        return s + Math.round(Math.round(del * 0.78) * Number(d.commission_rate) / 100);
      }, 0)) + ".0000",
    },
  },
  detail: {
    start_date: date(-30),
    end_date: date(0),
    results: MOCK_DISTRIBUTORS.flatMap((d, i) =>
      MOCK_PRODUCTS.slice(5, 9).map((p, j) => {
        const delivered = 120 + i * 30 + j * 15;
        const sold = Math.round(delivered * 0.7);
        const toStores = Math.round(delivered * 0.85);
        const returned = (i + 1) * 4 + j;
        return {
          distributor_id: d.id,
          distributor_name: d.name,
          product_id: p.id,
          product_name: p.name,
          product_code: p.code,
          qty_delivered: String(delivered),
          qty_sold: String(sold),
          qty_to_stores: String(toStores),
          qty_returned: String(returned),
          qty_balance: String(delivered - sold - returned),
        };
      })
    ),
  },
  commission: {
    start_date: date(-30),
    end_date: date(0),
    basis: "total",
    results: MOCK_DISTRIBUTORS.map((d, i) => {
      const sales = 35_000_000 + i * 9_500_000;
      const rate = Number(d.commission_rate);
      return {
        distributor_id: d.id,
        distributor_code: d.code,
        distributor_name: d.name,
        total_sales: String(sales) + ".0000",
        commission_rate: d.commission_rate,
        commission_amount: String(Math.round(sales * rate / 100)) + ".0000",
        settlement_status: i === 0 ? "unsettled" : "settled",
        basis: "total",
      };
    }),
    totals: {
      total_sales: String(MOCK_DISTRIBUTORS.reduce((s, _, i) => s + 35_000_000 + i * 9_500_000, 0)) + ".0000",
      commission_amount: String(MOCK_DISTRIBUTORS.reduce((s, d, i) => {
        const sales = 35_000_000 + i * 9_500_000;
        return s + Math.round(sales * Number(d.commission_rate) / 100);
      }, 0)) + ".0000",
    },
  },
};

// Helper for settlement_check by distributor_id (used by api.ts mock)
export function distributionSettlementCheck(distributorId: number) {
  const id = Number(distributorId);
  if (id === 1) {
    return {
      distributor_id: id,
      has_unsettled: true,
      unsettled_count: 2,
      warning: "این عامل پخش تحویل تسویه‌نشده دارد. لطفاً ابتدا تسویه کنید.",
    };
  }
  return {
    distributor_id: id,
    has_unsettled: false,
    unsettled_count: 0,
    warning: null,
  };
}

// ============================================================================
// D02-APP — اپلیکیشن موبایل عامل پخش (mobile PWA)
// ============================================================================

export const MOCK_DISTRIBUTOR_USER = {
  id: 4,
  username: "distributor1",
  email: "dist1@workshop.local",
  first_name: "عامل",
  last_name: "پخش مرکز",
  role: "distributor",
  display_name: "عامل پخش مرکز",
  distributor_id: 1,
  distributor_name: "عامل پخش مرکز",
  distributor_code: "D001",
};

// کالاهای در دست عامل پخش (از اقلام تحویل‌داده‌شده به او که هنوز نفروخته است)
export const MOCK_DISTRIBUTOR_PRODUCTS: Array<{
  id: number;
  dispatch_no: string;
  product_id: number;
  product_name: string;
  product_code: string;
  qty: string;
  unit_price: string;
  total_value: string;
  dispatch_date: string;
}> = MOCK_PRODUCTS.slice(5, 13).map((p, i) => {
  const qty = 24 + i * 8;
  const price = parseFloat(p.default_price);
  return {
    id: i + 1,
    dispatch_no: `D-${601 + (i % 3)}`,
    product_id: p.id,
    product_name: p.name,
    product_code: p.code,
    qty: String(qty),
    unit_price: p.default_price,
    total_value: String(qty * price) + ".0000",
    dispatch_date: date(-3 - (i % 5)),
  };
});

// فروش‌های ثبت‌شده توسط این عامل پخش
export const MOCK_DISTRIBUTOR_SALES: Array<{
  id: number;
  sale_no: string;
  store_id: number;
  store_name: string;
  sale_date: string;
  sales_type: "consignment" | "firm";
  sales_type_display: string;
  payment_method: string;
  payment_method_display: string;
  paid_amount: string;
  total_amount: string;
  status: string;
  status_display: string;
  notes: string;
  created_at: string;
  lines: Array<{
    id: number;
    product_id: number;
    product_name: string;
    qty: string;
    unit_price: string;
    line_total: string;
  }>;
}> = Array.from({ length: 6 }).map((_, i) => {
  const id = 100 + i;
  const store = MOCK_STORES[i % MOCK_STORES.length];
  const salesType: "consignment" | "firm" = i % 2 === 0 ? "consignment" : "firm";
  const paymentMethod = (["cash", "card", "bank_transfer", "check"] as const)[i % 4];
  const lines = MOCK_PRODUCTS.slice(5 + (i % 3), 5 + (i % 3) + 1 + (i % 2)).map((p, j) => {
    const qty = 6 + ((i + j) * 4) % 22;
    const price = parseFloat(p.default_price);
    return {
      id: id * 10 + j,
      product_id: p.id,
      product_name: p.name,
      qty: String(qty),
      unit_price: p.default_price,
      line_total: String(qty * price) + ".0000",
    };
  });
  const total = lines.reduce((s, l) => s + parseFloat(l.line_total), 0);
  return {
    id,
    sale_no: `S-${1402 + i}`,
    store_id: store.id,
    store_name: store.name,
    sale_date: date(-i),
    sales_type: salesType,
    sales_type_display: salesType === "consignment" ? "امانی" : "قطعی",
    payment_method: paymentMethod,
    payment_method_display:
      { cash: "نقد", card: "کارت", bank_transfer: "انتقال بانکی", check: "چک" }[paymentMethod],
    paid_amount: salesType === "firm" ? String(total) + ".0000" : "0.0000",
    total_amount: String(total) + ".0000",
    status: i === 0 ? "draft" : "posted",
    status_display: i === 0 ? "در انتظار" : "ثبت شد",
    notes: i === 0 ? "تحویل اولیه صبح" : "",
    created_at: iso(-i, 10 + i),
    lines,
  };
});

// گزارش‌های عامل پخش
export const MOCK_DISTRIBUTOR_REPORTS = {
  // گزارش فروش من
  my_sales: {
    period_days: 30,
    total_sales: String(
      MOCK_DISTRIBUTOR_SALES.reduce((s, x) => s + parseFloat(x.total_amount), 0)
    ) + ".0000",
    total_count: MOCK_DISTRIBUTOR_SALES.length,
    avg_sale: String(
      Math.round(
        MOCK_DISTRIBUTOR_SALES.reduce((s, x) => s + parseFloat(x.total_amount), 0) /
          Math.max(1, MOCK_DISTRIBUTOR_SALES.length)
      )
    ) + ".0000",
    consignment_count: MOCK_DISTRIBUTOR_SALES.filter((s) => s.sales_type === "consignment").length,
    firm_count: MOCK_DISTRIBUTOR_SALES.filter((s) => s.sales_type === "firm").length,
    results: MOCK_DISTRIBUTOR_SALES.map((s) => ({
      sale_id: s.id,
      sale_no: s.sale_no,
      sale_date: s.sale_date,
      store_name: s.store_name,
      total_amount: s.total_amount,
      sales_type: s.sales_type,
      sales_type_display: s.sales_type_display,
      status: s.status,
      status_display: s.status_display,
    })),
  },
  // گزارش پورسانت
  commission: {
    period_days: 30,
    distributor_id: 1,
    distributor_name: "عامل پخش مرکز",
    distributor_code: "D001",
    commission_rate: "5.00",
    total_sales: String(
      MOCK_DISTRIBUTOR_SALES.reduce((s, x) => s + parseFloat(x.total_amount), 0)
    ) + ".0000",
    commission_owed: String(
      Math.round(
        MOCK_DISTRIBUTOR_SALES.reduce((s, x) => s + parseFloat(x.total_amount), 0) * 0.05
      )
    ) + ".0000",
    commission_paid: "1200000.0000",
    balance: String(
      Math.round(
        MOCK_DISTRIBUTOR_SALES.reduce((s, x) => s + parseFloat(x.total_amount), 0) * 0.05
      ) - 1_200_000
    ) + ".0000",
  },
  // مانده کالا
  product_balance: {
    distributor_id: 1,
    distributor_name: "عامل پخش مرکز",
    total_qty: String(
      MOCK_DISTRIBUTOR_PRODUCTS.reduce((s, p) => s + parseFloat(p.qty), 0)
    ),
    total_value: String(
      MOCK_DISTRIBUTOR_PRODUCTS.reduce((s, p) => s + parseFloat(p.total_value), 0)
    ) + ".0000",
    results: MOCK_DISTRIBUTOR_PRODUCTS.map((p) => ({
      product_id: p.product_id,
      product_name: p.product_name,
      product_code: p.product_code,
      qty: p.qty,
      unit_price: p.unit_price,
      total_value: p.total_value,
      dispatch_no: p.dispatch_no,
      dispatch_date: p.dispatch_date,
    })),
  },
};

// فروشگاه‌های تخصیص‌یافته به عامل پخش فعلی (برای استفاده در فرم فروش جدید)
export const MOCK_DISTRIBUTOR_STORES = MOCK_STORES.slice(0, 4).map((s) => ({
  ...s,
  distributor_id: 1,
}));
