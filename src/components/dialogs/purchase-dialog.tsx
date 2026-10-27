"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2, CalendarDays, Globe } from "lucide-react";
import { api, type Paginated, ApiError } from "@/lib/api";
import {
  MOCK_CONTRACTORS,
  MOCK_WAREHOUSES,
  MOCK_PRODUCTS,
  MOCK_ACCOUNTS,
  MOCK_UNITS,
} from "@/lib/mock-data";
import { formatNumber, formatRial } from "@/lib/format";
import { numberToPersianWords } from "@/lib/number-to-words";
import { addDaysISO, todayISO, formatDate, getCalendarMode, type CalendarMode } from "@/lib/calendar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DatePicker } from "@/components/dialogs/datepicker";

type Contractor = (typeof MOCK_CONTRACTORS)[number];
type Warehouse = (typeof MOCK_WAREHOUSES)[number];
type Product = (typeof MOCK_PRODUCTS)[number] & {
  unit?: number | null;
  unit_code?: string;
  unit_name?: string;
  is_finished_good?: boolean;
};
type Account = (typeof MOCK_ACCOUNTS)[number];
type Unit = (typeof MOCK_UNITS)[number];

interface PurchaseLine {
  product_id: number | null;
  product_name: string;        // نام تایپ‌شده توسط کاربر (برای محصول جدید یا نمایش)
  product_code?: string;       // کد محصول جدید (اختیاری)
  qty: string;
  unit_id: number | null;
  unit_price: string;
  shelf_life_days: number;
  is_new_product: boolean;     // آیا محصول جدید است (تایپ‌شده، نه انتخاب‌شده از لیست)
}

interface PurchaseDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

const STEPS = [
  { id: 1, label: "سربرگ خرید" },
  { id: 2, label: "اقلام خرید" },
  { id: 3, label: "خلاصه و ذخیره" },
];

// ─── PriceInput: فیلد قیمت با جداکننده هزارگان + نمایش حروفی (تومان) ──────────
interface PriceInputProps {
  value: string;
  onChange: (raw: string) => void;
}

function PriceInput({ value, onChange }: PriceInputProps) {
  // نمایش با جداکننده هزارگان
  const displayValue = React.useMemo(() => {
    const num = parseFloat(value || "0");
    if (isNaN(num) || num === 0) return "";
    return num.toLocaleString("en-US");
  }, [value]);

  // نمایش حروفی به تومان (هر ۱۰ ریال = ۱ تومان)
  const words = React.useMemo(() => {
    const num = parseFloat(value || "0");
    if (isNaN(num) || num === 0) return "";
    const toman = Math.floor(num / 10);
    return `${numberToPersianWords(toman)} تومان`;
  }, [value]);

  return (
    <div className="flex flex-col gap-0.5 min-w-[140px]">
      <Input
        dir="ltr"
        className="nums w-full"
        type="text"
        inputMode="numeric"
        value={displayValue}
        onChange={(e) => {
          const raw = e.target.value.replace(/[^\d]/g, "");
          onChange(raw);
        }}
        placeholder="0"
      />
      {words && (
        <span className="text-xs text-red-600 leading-tight font-medium" dir="rtl">
          {words}
        </span>
      )}
    </div>
  );
}

// ─── LineTotalDisplay: نمایش جمع خط با حروفی ──────────
function LineTotalDisplay({ qty, unitPrice }: { qty: string; unitPrice: string }) {
  const total = parseFloat(qty || "0") * parseFloat(unitPrice || "0");
  const display = total > 0 ? total.toLocaleString("en-US") : "0";
  const words = React.useMemo(() => {
    if (total <= 0) return "";
    const toman = Math.floor(total / 10);
    return `${numberToPersianWords(toman)} تومان`;
  }, [total]);
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs nums font-mono" dir="ltr">{display}</span>
      {words && (
        <span className="text-xs text-red-600 leading-tight font-medium" dir="rtl">
          {words}
        </span>
      )}
    </div>
  );
}

// ─── ProductCombobox: تایپ + پیشنهاد + ساخت محصول جدید ───────────────
interface ProductComboboxProps {
  value: number | null;
  productName: string;
  isNew: boolean;
  products: Product[];
  onChange: (selection: { type: "existing"; id: number; name: string } | { type: "new"; name: string }) => void;
}

function ProductCombobox({ value, productName, isNew, products, onChange }: ProductComboboxProps) {
  const [query, setQuery] = React.useState("");
  const [open, setOpen] = React.useState(false);

  // نام نمایشی در input
  const displayValue = isNew
    ? productName
    : (products.find((p) => p.id === value)?.name ?? productName ?? "");

  // فیلتر پیشنهادات بر اساس تایپ کاربر
  const filtered = React.useMemo(() => {
    if (!query.trim()) return products.slice(0, 10);
    const q = query.toLowerCase();
    return products
      .filter((p) =>
        p.name.toLowerCase().includes(q) ||
        p.code.toLowerCase().includes(q) ||
        (p.barcode ?? "").includes(q)
      )
      .slice(0, 10);
  }, [products, query]);

  // آیا نام تایپ‌شده با هیچ محصولی دقیقاً match نمی‌شه؟
  const exactMatch = query.trim() ? products.find((p) => p.name === query.trim()) : null;
  const showNewOption = query.trim() && !exactMatch && filtered.length === 0;

  // وقتی popover بسته می‌شه، اگه query خالی نیست و کالایی انتخاب نشده، خودکار کالای جدید بساز
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen && query.trim() && !value && !isNew) {
      // کاربر تایپ کرده ولی کالایی انتخاب نکرده — به‌عنوان کالای جدید در نظر بگیر
      onChange({ type: "new", name: query.trim() });
      setQuery("");
    }
    setOpen(newOpen);
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className="w-44 justify-start font-normal"
          dir="rtl"
        >
          {displayValue || <span className="text-muted-foreground">نام کالا را تایپ کنید…</span>}
          {isNew && <Badge variant="secondary" className="ml-1 text-[10px]">جدید</Badge>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-0" align="start">
        <div className="p-2 border-b">
          <Input
            autoFocus
            placeholder="نام کالا را تایپ کنید…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              // اگه Enter زد و فقط یک پیشنهاد بود، انتخابش کن
              if (e.key === "Enter" && filtered.length === 1) {
                const p = filtered[0];
                onChange({ type: "existing", id: p.id, name: p.name });
                setQuery("");
                setOpen(false);
              }
              // اگه Enter زد و پیشنهادی نبود، کالای جدید بساز
              else if (e.key === "Enter" && query.trim() && filtered.length === 0) {
                onChange({ type: "new", name: query.trim() });
                setQuery("");
                setOpen(false);
              }
            }}
            dir="rtl"
          />
        </div>
        <div className="max-h-60 overflow-y-auto scroll-pretty">
          {filtered.length === 0 && !query.trim() ? (
            <div className="p-3 text-center text-sm text-muted-foreground">
              شروع به تایپ کنید…
            </div>
          ) : filtered.length === 0 && query.trim() ? (
            <button
              type="button"
              className="flex w-full items-center gap-2 bg-primary/5 px-3 py-2 text-sm hover:bg-primary/10 text-right"
              onClick={() => {
                onChange({ type: "new", name: query.trim() });
                setQuery("");
                setOpen(false);
              }}
            >
              <Plus className="h-4 w-4 text-primary" />
              <span>افزودن «{query.trim()}» به‌عنوان کالای جدید</span>
            </button>
          ) : (
            <>
              {filtered.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-accent text-right"
                  onClick={() => {
                    onChange({ type: "existing", id: p.id, name: p.name });
                    setQuery("");
                    setOpen(false);
                  }}
                >
                  <span className="font-medium">{p.name}</span>
                  <span className="text-xs text-muted-foreground font-mono" dir="ltr">{p.code}</span>
                </button>
              ))}
              {query.trim() && !exactMatch && (
                <button
                  type="button"
                  className="flex w-full items-center gap-2 border-t bg-primary/5 px-3 py-2 text-sm hover:bg-primary/10 text-right"
                  onClick={() => {
                    onChange({ type: "new", name: query.trim() });
                    setQuery("");
                    setOpen(false);
                  }}
                >
                  <Plus className="h-4 w-4 text-primary" />
                  <span>افزودن «{query.trim()}» به‌عنوان کالای جدید</span>
                </button>
              )}
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

export function PurchaseDialog({ open, onOpenChange }: PurchaseDialogProps) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);
  const [purchaseDate, setPurchaseDate] = React.useState<string | null>(todayISO());
  // R2: calendar mode state — default Jalali, toggle to Gregorian
  const [calMode, setCalMode] = React.useState<CalendarMode>(getCalendarMode());
  const [contractorId, setContractorId] = React.useState<string>("");
  const [warehouseId, setWarehouseId] = React.useState<string>("");
  const [cashAccountId, setCashAccountId] = React.useState<string>("");
  const [notes, setNotes] = React.useState("");
  const [lines, setLines] = React.useState<PurchaseLine[]>([
    { product_id: null, product_name: "", product_code: "", qty: "0", unit_id: null, unit_price: "0", shelf_life_days: 30, is_new_product: false },
  ]);

  const { data: contractors } = useQuery({
    queryKey: ["contractors-options"],
    queryFn: () => api<Paginated<Contractor>>("/workshop/contractors/", { query: { page: 1, page_size: 100 } }),
  });
  // R6: fetch ALL warehouses (no type filter) — user wants to select from all
  const { data: warehouses } = useQuery({
    queryKey: ["warehouses-all"],
    queryFn: () => api<Paginated<Warehouse>>("/inventory/warehouses/", { query: { page: 1, page_size: 200 } }),
  });
  const { data: products, refetch: refetchProducts } = useQuery({
    queryKey: ["products-options", "raw"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 200, is_finished_good: false } }),
  });
  const { data: unitsData } = useQuery({
    queryKey: ["units-options"],
    queryFn: () => api<Paginated<Unit>>("/products/units/", { query: { page: 1, page_size: 100 } }),
  });
  const { data: accounts } = useQuery({
    queryKey: ["accounts-cash"],
    queryFn: () => api<{ results: Account[] } | Account[]>("/accounting/accounts/", { query: { type: "asset" } }),
  });

  // R6: show ALL warehouses, not just raw_materials
  const allWarehouses = warehouses?.results ?? MOCK_WAREHOUSES;
  const cashAccounts = Array.isArray(accounts) ? accounts : accounts?.results ?? MOCK_ACCOUNTS;
  const contractorList = contractors?.results ?? MOCK_CONTRACTORS;
  const productList = products?.results ?? MOCK_PRODUCTS;
  const unitList = unitsData?.results ?? MOCK_UNITS;

  // Build product-id → unit map for auto-selecting unit when product chosen
  const productUnitMap = React.useMemo(() => {
    const m = new Map<number, number | null>();
    productList.forEach((p: any) => {
      const uid = typeof p.unit === "number" ? p.unit : (p.unit?.id ?? null);
      if (uid !== null) m.set(p.id, uid);
    });
    return m;
  }, [productList]);

  const totalAmount = React.useMemo(
    () =>
      lines.reduce((s, l) => s + (parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0")), 0),
    [lines]
  );
  const totalQty = React.useMemo(
    () => lines.reduce((s, l) => s + parseFloat(l.qty || "0"), 0),
    [lines]
  );

  const mutation = useMutation({
    mutationFn: () => {
      // R4: build payload defensively, convert empty strings to 0
      const payload = {
        purchase_date: purchaseDate,
        contractor: Number(contractorId),
        warehouse: Number(warehouseId),
        cash_account: Number(cashAccountId),
        notes: notes || "",
        lines: lines
          .filter((l) => l.product_id !== null || l.product_name.trim() !== "")
          .map((l, i) => ({
            product_id: l.product_id,
            product_name: l.is_new_product ? l.product_name.trim() : undefined,
            product_code: l.is_new_product ? (l.product_code?.trim() || undefined) : undefined,
            qty: String(l.qty || "0"),
            unit_price: String(l.unit_price || "0"),
            shelf_life_days: Number(l.shelf_life_days) || 30,
            expiry_date: addDaysISO(purchaseDate, l.shelf_life_days),
            lot_no: `PUR-${String(Date.now()).slice(-4)}-${i + 1}`,
            unit_id: l.unit_id ?? undefined,
          })),
      };
      return api("/workshop/purchases/create_purchase/", { method: "POST", body: payload });
    },
    onSuccess: () => {
      toast.success("خرید با موفقیت ثبت شد.");
      qc.invalidateQueries({ queryKey: ["purchases"] });
      // رفرش لیست محصولات تا کالای جدید ساخته‌شده هم نشون داده بشه
      qc.invalidateQueries({ queryKey: ["products-options"] });
      onOpenChange(false);
      reset();
    },
    onError: (e: unknown) => {
      // R4: detailed error message from backend
      let msg = "خطا در ثبت خرید.";
      if (e instanceof ApiError) {
        if (typeof e.detail === "string") {
          msg = e.detail;
        } else if (e.detail && typeof e.detail === "object") {
          // field-level errors from DRF
          msg = Object.entries(e.detail as Record<string, unknown>)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`)
            .join(" | ");
        } else {
          msg = `خطای HTTP ${e.status}`;
        }
      } else if (e instanceof Error) {
        msg = e.message;
      }
      toast.error(msg);
      console.error("Purchase error:", e);
    },
  });

  const reset = () => {
    setStep(1);
    setPurchaseDate(todayISO());
    setCalMode(getCalendarMode());
    setContractorId("");
    setWarehouseId("");
    setCashAccountId("");
    setNotes("");
    setLines([{ product_id: null, product_name: "", product_code: "", qty: "0", unit_id: null, unit_price: "0", shelf_life_days: 30, is_new_product: false }]);
  };

  const canStep1 = purchaseDate && contractorId && warehouseId && cashAccountId;
  const canStep2 = lines.length > 0 && lines.every((l) =>
    (l.product_id !== null || l.product_name.trim() !== "") &&
    parseFloat(l.qty) > 0 &&
    parseFloat(l.unit_price) >= 0
  );

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>خرید مواد اولیه</DialogTitle>
          <DialogDescription>ثبت سند خرید از کارپرداز/تأمین‌کننده</DialogDescription>
        </DialogHeader>

        {/* Stepper */}
        <div className="flex items-center gap-2 text-xs">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              <button
                type="button"
                onClick={() => setStep(s.id)}
                className={`flex items-center gap-2 rounded-full border px-3 py-1 ${
                  step === s.id ? "border-primary bg-primary/5 text-primary" : "text-muted-foreground"
                }`}
              >
                <span className="font-mono nums">{s.id}</span>
                <span>{s.label}</span>
              </button>
              {i < STEPS.length - 1 && <span className="text-muted-foreground">←</span>}
            </React.Fragment>
          ))}
        </div>

        {step === 1 && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              {/* R2: Calendar mode toggle (Jalali/Gregorian) */}
              <div className="flex items-center justify-between">
                <Label>تاریخ خرید</Label>
                <div className="flex items-center gap-1">
                  <Button
                    type="button"
                    variant={calMode === "jalali" ? "default" : "outline"}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setCalMode("jalali")}
                  >
                    <CalendarDays className="h-3 w-3 ml-1" /> شمسی
                  </Button>
                  <Button
                    type="button"
                    variant={calMode === "gregorian" ? "default" : "outline"}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setCalMode("gregorian")}
                  >
                    <Globe className="h-3 w-3 ml-1" /> میلادی
                  </Button>
                </div>
              </div>
              <DatePicker value={purchaseDate} onChange={setPurchaseDate} mode={calMode} />
              {purchaseDate && (
                <p className="text-xs text-muted-foreground">
                  نمایش: {formatDate(purchaseDate, calMode)} — ذخیره در سرور: {purchaseDate}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label>کارپرداز</Label>
              <Select value={contractorId} onValueChange={setContractorId}>
                <SelectTrigger><SelectValue placeholder="انتخاب کارپرداز" /></SelectTrigger>
                <SelectContent>
                  {contractorList.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>{c.name} — {c.code}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* محل تحویل (انبار) — همه‌ی انبارها قابل انتخاب */}
            <div className="space-y-1.5">
              <Label>محل تحویل (انبار)</Label>
              <Select value={warehouseId} onValueChange={setWarehouseId}>
                <SelectTrigger><SelectValue placeholder="انتخاب انبار" /></SelectTrigger>
                <SelectContent>
                  {/* R6: show ALL warehouses (with type badge) */}
                  {allWarehouses.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>
                      {w.name} {w.type ? `(${w.type === "raw_materials" ? "مواد اولیه" : w.type === "finished_goods" ? "محصول" : w.type === "workshop" ? "کارگاه" : w.type === "main" ? "اصلی" : w.type === "store" ? "فروشگاه" : "مجازی"})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>حساب پرداختی (صندوق/بانک)</Label>
              <Select value={cashAccountId} onValueChange={setCashAccountId}>
                <SelectTrigger><SelectValue placeholder="انتخاب حساب" /></SelectTrigger>
                <SelectContent>
                  {cashAccounts.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>{a.name} — {a.code}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="pur-notes">توضیحات</Label>
              <Textarea id="pur-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="مثلاً: خرید نقدی آرد" />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                    <TableHead className="text-right">واحد</TableHead>
                    <TableHead className="text-right">قیمت واحد</TableHead>
                    <TableHead className="text-right">عمر (روز)</TableHead>
                    <TableHead className="text-right">تاریخ انقضا</TableHead>
                    <TableHead className="text-right">جمع خط</TableHead>
                    <TableHead className="text-right w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((l, idx) => {
                    const expiry = addDaysISO(purchaseDate, l.shelf_life_days);
                    const lineTotal = parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0");
                    return (
                      <TableRow key={idx}>
                        <TableCell>
                          <ProductCombobox
                            value={l.product_id}
                            productName={l.product_name}
                            isNew={l.is_new_product}
                            products={productList}
                            onChange={(selection) => {
                              if (selection.type === "existing") {
                                const defaultUnitId = productUnitMap.get(selection.id) ?? null;
                                updateLine(idx, {
                                  product_id: selection.id,
                                  product_name: selection.name,
                                  unit_id: defaultUnitId,
                                  is_new_product: false,
                                });
                              } else {
                                // محصول جدید — نام تایپ‌شده
                                // واحد پیش‌فرض: NUM (عدد) اگه کاربر هنوز واحدی انتخاب نکرده
                                const defaultUnitId = l.unit_id ?? unitList.find((u: any) => u.code === "NUM")?.id ?? null;
                                updateLine(idx, {
                                  product_id: null,
                                  product_name: selection.name,
                                  is_new_product: true,
                                  unit_id: defaultUnitId,
                                });
                              }
                            }}
                          />
                        </TableCell>
                        <TableCell>
                          <Input dir="ltr" className="nums w-20" type="number" value={l.qty} onChange={(e) => updateLine(idx, { qty: e.target.value })} />
                        </TableCell>
                        <TableCell>
                          <Select
                            value={l.unit_id ? String(l.unit_id) : ""}
                            onValueChange={(v) => updateLine(idx, { unit_id: Number(v) })}
                          >
                            <SelectTrigger className="w-28"><SelectValue placeholder="واحد" /></SelectTrigger>
                            <SelectContent>
                              {unitList.map((u) => (
                                <SelectItem key={u.id} value={String(u.id)}>{u.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <PriceInput
                            value={l.unit_price}
                            onChange={(v) => updateLine(idx, { unit_price: v })}
                          />
                        </TableCell>
                        <TableCell>
                          <Input dir="ltr" className="nums w-20" type="number" value={l.shelf_life_days} onChange={(e) => updateLine(idx, { shelf_life_days: Number(e.target.value) })} />
                        </TableCell>
                        <TableCell className="text-xs nums" dir="ltr">{formatDate(expiry, calMode)}</TableCell>
                        <TableCell>
                          <LineTotalDisplay qty={l.qty} unitPrice={l.unit_price} />
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" onClick={() => removeLine(idx)} disabled={lines.length === 1}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <Button variant="outline" onClick={addLine}>
              <Plus className="h-4 w-4" /> افزودن قلم
            </Button>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            {/* R3: invoice-style summary */}
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground">شماره فاکتور:</span>
                  <span className="font-medium font-mono nums mr-2" dir="ltr">PUR-{String(Date.now()).slice(-6)}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">تاریخ:</span>
                  <span className="font-medium nums mr-2" dir="ltr">{formatDate(purchaseDate, calMode)}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">کارپرداز:</span>
                  <span className="font-medium mr-2">{contractorList.find((c) => c.id === Number(contractorId))?.name ?? "—"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">محل تحویل:</span>
                  <span className="font-medium mr-2">{allWarehouses.find((w) => w.id === Number(warehouseId))?.name ?? "—"}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-muted-foreground">حساب پرداختی:</span>
                  <span className="font-medium mr-2">{cashAccounts.find((a) => a.id === Number(cashAccountId))?.name ?? "—"}</span>
                </div>
              </div>
            </div>

            {/* R3: invoice-style table (ردیف/شرح کالا/مقدار/فی/قیمت کل) */}
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right w-12">ردیف</TableHead>
                    <TableHead className="text-right">شرح کالا</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                    <TableHead className="text-right">واحد</TableHead>
                    <TableHead className="text-right">فی</TableHead>
                    <TableHead className="text-right">قیمت کل</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.filter((l) => l.product_id !== null || (l.is_new_product && l.product_name.trim() !== "")).map((l, i) => {
                    const prodName = l.is_new_product
                      ? l.product_name
                      : (productList.find((p) => p.id === l.product_id)?.name ?? l.product_name ?? "—");
                    const unitName = unitList.find((u) => u.id === l.unit_id)?.name ?? "—";
                    const lineTotal = parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0");
                    return (
                      <TableRow key={i}>
                        <TableCell className="font-mono nums">{i + 1}</TableCell>
                        <TableCell className="font-medium">
                          {prodName}
                          {l.is_new_product && <Badge variant="secondary" className="mr-2 text-[10px]">جدید</Badge>}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(parseFloat(l.qty || "0"))}</TableCell>
                        <TableCell>{unitName}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(parseFloat(l.unit_price || "0"))}</TableCell>
                        <TableCell className="nums font-semibold" dir="ltr">{formatRial(lineTotal)}</TableCell>
                      </TableRow>
                    );
                  })}
                  <TableRow className="border-t-2 bg-muted/50">
                    <TableCell colSpan={4} className="text-left font-semibold">جمع کل:</TableCell>
                    <TableCell className="nums font-bold" dir="ltr">{formatNumber(totalQty)}</TableCell>
                    <TableCell className="nums font-bold text-primary" dir="ltr">{formatRial(totalAmount)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        <DialogFooter className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>انصراف</Button>
          <div className="flex items-center gap-2">
            {step > 1 && (
              <Button variant="outline" onClick={() => setStep((s) => Math.max(1, s - 1))}>قبلی</Button>
            )}
            {step < 3 && (
              <Button
                disabled={step === 1 ? !canStep1 : !canStep2}
                onClick={() => setStep((s) => Math.min(3, s + 1))}
              >
                بعدی
              </Button>
            )}
            {step === 3 && (
              <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !canStep2}>
                {mutation.isPending ? "در حال ذخیره…" : "ذخیره خرید"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  function updateLine(idx: number, patch: Partial<PurchaseLine>) {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  function addLine() {
    setLines((prev) => [...prev, { product_id: null, product_name: "", product_code: "", qty: "0", unit_id: null, unit_price: "0", shelf_life_days: 30, is_new_product: false }]);
  }
  function removeLine(idx: number) {
    setLines((prev) => prev.filter((_, i) => i !== idx));
  }
}
