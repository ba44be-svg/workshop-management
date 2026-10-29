"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Store as StoreIcon,
  Package,
  Plus,
  Trash2,
  ShoppingCart,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Banknote,
  CreditCard,
  FileCheck,
  ArrowLeftRight,
  Loader2,
  Check,
  ClipboardList,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { formatRial, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

interface Store {
  id: number;
  code: string;
  name: string;
  address: string;
  phone: string;
  tier_display: string;
  sales_model_display: string;
}

interface DispatchLine {
  id: number;
  product_id: number;
  product_name: string;
  product_code: string;
  qty: string;
  unit_price: string;
  line_total: string;
}

interface DispatchItem {
  id: number;
  dispatch_no: string;
  dispatch_date: string;
  total_amount: string;
  lines: DispatchLine[];
}

interface DispatchesResponse {
  count: number;
  results: DispatchItem[];
}

interface CartItem {
  line: DispatchLine;
  qty: number; // user input
  unit_price: number; // user input
}

type SalesType = "consignment" | "firm";
type PaymentMethod = "cash" | "check" | "card" | "bank_transfer";

const PAYMENT_METHODS: Array<{
  value: PaymentMethod;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { value: "cash", label: "نقد", icon: Banknote },
  { value: "card", label: "کارت", icon: CreditCard },
  { value: "check", label: "چک", icon: FileCheck },
  { value: "bank_transfer", label: "انتقال بانکی", icon: ArrowLeftRight },
];

export function NewSale({ onDone }: { onDone: () => void }) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState<1 | 2 | 3 | 4>(1);
  const [storeId, setStoreId] = React.useState<number | null>(null);
  const [cart, setCart] = React.useState<CartItem[]>([]);
  const [salesType, setSalesType] = React.useState<SalesType>("consignment");
  const [paymentMethod, setPaymentMethod] = React.useState<PaymentMethod>("cash");
  const [paidAmount, setPaidAmount] = React.useState<string>("");
  const [notes, setNotes] = React.useState("");

  // Fetch stores assigned to this distributor
  const { data: storesRes, isLoading: storesLoading } = useQuery({
    queryKey: ["distributor", "stores"],
    queryFn: () =>
      api<{ count: number; results: Store[] }>("/partners/stores/my/"),
  });

  // Fetch products in hand
  const { data: dispatchRes, isLoading: dispatchLoading } = useQuery({
    queryKey: ["distributor", "my_dispatches"],
    queryFn: () => api<DispatchesResponse>("/dispatch/my_dispatches/"),
  });

  const inHandProducts = React.useMemo(() => {
    const out: DispatchLine[] = [];
    for (const d of dispatchRes?.results ?? []) {
      for (const l of d.lines ?? []) out.push(l);
    }
    return out;
  }, [dispatchRes]);

  const cartTotal = cart.reduce(
    (s, c) => s + c.qty * c.unit_price,
    0
  );

  const addToCart = (line: DispatchLine) => {
    setCart((prev) => {
      const exists = prev.find((c) => c.line.id === line.id);
      if (exists) return prev; // already added
      return [
        ...prev,
        {
          line,
          qty: 1,
          unit_price: parseFloat(line.unit_price ?? "0"),
        },
      ];
    });
    toast.success(`${line.product_name} به سبد اضافه شد.`);
  };

  const updateQty = (lineId: number, qty: number) => {
    setCart((prev) =>
      prev.map((c) => (c.line.id === lineId ? { ...c, qty: Math.max(0, qty) } : c))
    );
  };

  const updatePrice = (lineId: number, price: number) => {
    setCart((prev) =>
      prev.map((c) =>
        c.line.id === lineId ? { ...c, unit_price: Math.max(0, price) } : c
      )
    );
  };

  const removeFromCart = (lineId: number) => {
    setCart((prev) => prev.filter((c) => c.line.id !== lineId));
  };

  const submitMutation = useMutation({
    mutationFn: () =>
      api("/sales/create/", {
        method: "POST",
        body: {
          store_id: storeId,
          sales_type: salesType,
          payment_method: paymentMethod,
          paid_amount: paidAmount || "0",
          notes,
          lines: cart.map((c) => ({
            product_id: c.line.product_id,
            qty: String(c.qty),
            unit_price: String(c.unit_price),
          })),
        },
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["distributor", "my_sales"] });
      qc.invalidateQueries({ queryKey: ["distributor", "my_dispatches"] });
      toast.success("فروش با موفقیت ثبت شد.");
      // Reset state
      setStoreId(null);
      setCart([]);
      setPaidAmount("");
      setNotes("");
      setSalesType("consignment");
      setPaymentMethod("cash");
      onDone();
    },
    onError: (err: Error) => {
      toast.error(err.message || "خطا در ثبت فروش.");
    },
  });

  const canNext = (s: 1 | 2 | 3 | 4): boolean => {
    if (s === 1) return storeId !== null;
    if (s === 2) return cart.length > 0 && cart.every((c) => c.qty > 0);
    if (s === 3) return !!salesType && !!paymentMethod;
    return true;
  };

  const next = () => setStep((s) => (s < 4 ? ((s + 1) as 1 | 2 | 3 | 4) : s));
  const prev = () => setStep((s) => (s > 1 ? ((s - 1) as 1 | 2 | 3 | 4) : s));

  return (
    <div className="space-y-4">
      {/* Stepper header */}
      <div className="flex items-center justify-between gap-1">
        {[
          { n: 1, label: "فروشگاه" },
          { n: 2, label: "کالاها" },
          { n: 3, label: "پرداخت" },
          { n: 4, label: "بازبینی" },
        ].map((s, i) => (
          <React.Fragment key={s.n}>
            <button
              onClick={() => s.n < step && setStep(s.n as 1 | 2 | 3 | 4)}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 rounded-xl py-2 transition-all",
                step === s.n
                  ? "bg-emerald-600 text-white shadow-md"
                  : s.n < step
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold",
                  step === s.n
                    ? "bg-white/20"
                    : s.n < step
                    ? "bg-emerald-200 text-emerald-800"
                    : "bg-muted-foreground/20"
                )}
              >
                {s.n < step ? <Check className="h-3.5 w-3.5" /> : s.n}
              </span>
              <span className="text-[10px] font-medium">{s.label}</span>
            </button>
            {i < 3 && (
              <div
                className={cn(
                  "h-0.5 flex-1 rounded-full",
                  s.n < step ? "bg-emerald-400" : "bg-muted"
                )}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -12 }}
          transition={{ duration: 0.2 }}
        >
          {/* STEP 1: select store */}
          {step === 1 && (
            <div className="space-y-3">
              <div>
                <h2 className="text-lg font-bold">فروشگاه را انتخاب کنید</h2>
                <p className="text-xs text-muted-foreground">
                  فقط فروشگاه‌های تخصیص‌یافته به شما نمایش داده می‌شوند.
                </p>
              </div>
              {storesLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full rounded-2xl" />
                  ))}
                </div>
              ) : (storesRes?.results ?? []).length === 0 ? (
                <div className="rounded-2xl border border-dashed bg-muted/30 p-6 text-center">
                  <StoreIcon className="mx-auto h-10 w-10 text-muted-foreground" />
                  <p className="mt-2 text-sm font-medium">فروشگاهی یافت نشد</p>
                  <p className="text-xs text-muted-foreground">
                    هیچ فروشگاهی به شما تخصیص نیافته است.
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {(storesRes?.results ?? []).map((s) => {
                    const active = storeId === s.id;
                    return (
                      <button
                        key={s.id}
                        onClick={() => setStoreId(s.id)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-2xl border p-3 text-right transition-all",
                          active
                            ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500/20"
                            : "border-border bg-white hover:border-emerald-300"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-xl",
                            active
                              ? "bg-emerald-600 text-white"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          <StoreIcon className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-sm font-semibold truncate">{s.name}</p>
                            {active && (
                              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
                            )}
                          </div>
                          <p className="text-[11px] text-muted-foreground truncate" dir="ltr">
                            {s.code} · {s.tier_display} · {s.sales_model_display}
                          </p>
                          {s.address && (
                            <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                              {s.address}
                            </p>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* STEP 2: add products */}
          {step === 2 && (
            <div className="space-y-3">
              <div>
                <h2 className="text-lg font-bold">کالاها را اضافه کنید</h2>
                <p className="text-xs text-muted-foreground">
                  از کالاهای در دست، مقدار و قیمت را وارد کنید.
                </p>
              </div>

              {/* Cart summary */}
              {cart.length > 0 && (
                <Card className="border-emerald-200 bg-emerald-50/40">
                  <CardContent className="p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-emerald-800">
                        سبد فروش ({cart.length} قلم)
                      </span>
                      <span className="text-base font-bold text-emerald-700 nums">
                        {formatRial(cartTotal)}
                      </span>
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {cart.map((c) => (
                        <div
                          key={c.line.id}
                          className="flex items-center gap-2 rounded-lg bg-white p-2"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">
                              {c.line.product_name}
                            </p>
                            <p className="text-[10px] text-muted-foreground nums">
                              {formatNumber(c.qty)} × {formatRial(c.unit_price)} ={" "}
                              <span className="font-bold text-emerald-700">
                                {formatRial(c.qty * c.unit_price)}
                              </span>
                            </p>
                          </div>
                          <button
                            onClick={() => removeFromCart(c.line.id)}
                            className="text-destructive hover:bg-destructive/10 p-1.5 rounded-lg"
                            aria-label="حذف"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Product list */}
              {dispatchLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-2xl" />
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {inHandProducts.map((line) => {
                    const inCart = cart.find((c) => c.line.id === line.id);
                    const availableQty = parseFloat(line.qty ?? "0");
                    return (
                      <Card
                        key={line.id}
                        className={cn(
                          "overflow-hidden transition-all",
                          inCart && "border-emerald-300 bg-emerald-50/30"
                        )}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-start gap-2.5">
                              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                                <Package className="h-5 w-5" />
                              </div>
                              <div>
                                <p className="text-sm font-semibold leading-tight">
                                  {line.product_name}
                                </p>
                                <p className="text-[11px] text-muted-foreground nums mt-0.5" dir="ltr">
                                  {line.product_code}
                                </p>
                                <p className="text-[11px] text-muted-foreground mt-0.5">
                                  موجودی:{" "}
                                  <span className="font-bold nums">
                                    {formatNumber(availableQty)}
                                  </span>
                                </p>
                              </div>
                            </div>
                            <Button
                              size="sm"
                              variant={inCart ? "secondary" : "default"}
                              onClick={() => addToCart(line)}
                              disabled={!!inCart}
                              className={
                                inCart
                                  ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-100"
                                  : "bg-emerald-600 hover:bg-emerald-700"
                              }
                            >
                              {inCart ? (
                                <>
                                  <Check className="h-4 w-4 ml-1" />
                                  اضافه شد
                                </>
                              ) : (
                                <>
                                  <Plus className="h-4 w-4 ml-1" />
                                  افزودن
                                </>
                              )}
                            </Button>
                          </div>

                          {inCart && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              className="mt-3 grid grid-cols-2 gap-2 border-t pt-3"
                            >
                              <div>
                                <Label className="text-[11px] text-muted-foreground">
                                  مقدار
                                </Label>
                                <Input
                                  type="number"
                                  inputMode="decimal"
                                  value={String(inCart.qty)}
                                  onChange={(e) =>
                                    updateQty(line.id, parseFloat(e.target.value) || 0)
                                  }
                                  className="h-9 mt-0.5 nums"
                                  dir="ltr"
                                  min={0}
                                  max={availableQty}
                                />
                              </div>
                              <div>
                                <Label className="text-[11px] text-muted-foreground">
                                  قیمت واحد (ریال)
                                </Label>
                                <Input
                                  type="number"
                                  inputMode="decimal"
                                  value={String(inCart.unit_price)}
                                  onChange={(e) =>
                                    updatePrice(line.id, parseFloat(e.target.value) || 0)
                                  }
                                  className="h-9 mt-0.5 nums"
                                  dir="ltr"
                                  min={0}
                                />
                              </div>
                              <div className="col-span-2 rounded-lg bg-muted/40 px-3 py-1.5 text-center">
                                <span className="text-[11px] text-muted-foreground ml-2">
                                  جمع این قلم:
                                </span>
                                <span className="text-sm font-bold text-emerald-700 nums">
                                  {formatRial(inCart.qty * inCart.unit_price)}
                                </span>
                              </div>
                            </motion.div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* STEP 3: payment details */}
          {step === 3 && (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold">جزئیات پرداخت</h2>
                <p className="text-xs text-muted-foreground">
                  نوع فروش و نحوه دریافت وجه را مشخص کنید.
                </p>
              </div>

              {/* Sales type */}
              <div>
                <Label className="text-sm font-medium mb-2 block">نوع فروش</Label>
                <RadioGroup
                  value={salesType}
                  onValueChange={(v) => setSalesType(v as SalesType)}
                  className="grid grid-cols-2 gap-2"
                >
                  <SalesTypeOption
                    value="consignment"
                    label="امانی"
                    description="کالا به فروشگاه سپرده می‌شود"
                    active={salesType === "consignment"}
                  />
                  <SalesTypeOption
                    value="firm"
                    label="قطعی"
                    description="فروش نقدی و قطعی"
                    active={salesType === "firm"}
                  />
                </RadioGroup>
              </div>

              {/* Payment method */}
              <div>
                <Label className="text-sm font-medium mb-2 block">نحوه دریافت وجه</Label>
                <div className="grid grid-cols-2 gap-2">
                  {PAYMENT_METHODS.map((p) => {
                    const Icon = p.icon;
                    const active = paymentMethod === p.value;
                    return (
                      <button
                        key={p.value}
                        type="button"
                        onClick={() => setPaymentMethod(p.value)}
                        className={cn(
                          "flex items-center gap-2 rounded-xl border p-3 text-sm transition-all",
                          active
                            ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500/20"
                            : "border-border bg-white hover:border-emerald-300"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-9 w-9 items-center justify-center rounded-lg",
                            active ? "bg-emerald-600 text-white" : "bg-muted text-muted-foreground"
                          )}
                        >
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className={cn("font-medium", active && "text-emerald-700")}>
                          {p.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Paid amount */}
              <div>
                <Label htmlFor="paid_amount" className="text-sm font-medium">
                  مبلغ دریافت‌شده (ریال)
                  <span className="text-[11px] text-muted-foreground mr-2">
                    {salesType === "consignment"
                      ? "(برای فروش امانی اختیاری)"
                      : "(برای فروش قطعی پیشنهاد می‌شود)"}
                  </span>
                </Label>
                <Input
                  id="paid_amount"
                  type="number"
                  inputMode="decimal"
                  value={paidAmount}
                  onChange={(e) => setPaidAmount(e.target.value)}
                  placeholder={String(Math.round(cartTotal))}
                  className="h-12 mt-1 nums"
                  dir="ltr"
                />
                <div className="mt-1.5 flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setPaidAmount(String(Math.round(cartTotal)))}
                  >
                    دریافت کامل ({formatRial(cartTotal)})
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setPaidAmount("0")}
                  >
                    صفر
                  </Button>
                </div>
              </div>

              {/* Notes */}
              <div>
                <Label htmlFor="notes" className="text-sm font-medium">
                  یادداشت (اختیاری)
                </Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="مثلاً: تحویل اول صبح، توضیحات فروشگاه، شماره چک و…"
                  rows={3}
                  className="mt-1"
                />
              </div>
            </div>
          )}

          {/* STEP 4: review & submit */}
          {step === 4 && (
            <div className="space-y-3">
              <div>
                <h2 className="text-lg font-bold">بازبینی و ثبت</h2>
                <p className="text-xs text-muted-foreground">
                  اطلاعات فروش را بررسی و ثبت نهایی کنید.
                </p>
              </div>

              {/* Summary cards */}
              <Card className="border-emerald-200">
                <CardContent className="p-3 space-y-2">
                  <SummaryRow
                    icon={<StoreIcon className="h-4 w-4" />}
                    label="فروشگاه"
                    value={
                      storesRes?.results.find((s) => s.id === storeId)?.name ?? "—"
                    }
                  />
                  <SummaryRow
                    icon={<ShoppingCart className="h-4 w-4" />}
                    label="تعداد اقلام"
                    value={String(cart.length)}
                  />
                  <SummaryRow
                    icon={<ClipboardList className="h-4 w-4" />}
                    label="نوع فروش"
                    value={salesType === "consignment" ? "امانی" : "قطعی"}
                  />
                  <SummaryRow
                    icon={<Banknote className="h-4 w-4" />}
                    label="نحوه دریافت"
                    value={
                      PAYMENT_METHODS.find((p) => p.value === paymentMethod)?.label ?? "نقد"
                    }
                  />
                  {paidAmount && parseFloat(paidAmount) > 0 && (
                    <SummaryRow
                      icon={<CheckCircle2 className="h-4 w-4" />}
                      label="مبلغ دریافت‌شده"
                      value={formatRial(paidAmount)}
                    />
                  )}
                  {notes && (
                    <SummaryRow
                      icon={<AlertCircle className="h-4 w-4" />}
                      label="یادداشت"
                      value={notes}
                    />
                  )}
                  <div className="border-t pt-2 mt-2 flex items-center justify-between">
                    <span className="text-sm font-semibold text-emerald-800">
                      مبلغ کل فروش
                    </span>
                    <span className="text-lg font-bold text-emerald-700 nums">
                      {formatRial(cartTotal)}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Line items */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-muted-foreground">
                  اقلام فروش:
                </p>
                {cart.map((c) => (
                  <div
                    key={c.line.id}
                    className="flex items-center justify-between rounded-lg border bg-white p-2.5"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {c.line.product_name}
                      </p>
                      <p className="text-[11px] text-muted-foreground nums" dir="ltr">
                        {formatNumber(c.qty)} × {formatRial(c.unit_price)}
                      </p>
                    </div>
                    <span className="text-sm font-bold text-emerald-700 nums">
                      {formatRial(c.qty * c.unit_price)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Footer nav */}
      <div className="flex items-center gap-2 pt-2">
        {step > 1 && (
          <Button variant="outline" className="h-12 flex-1" onClick={prev}>
            <ChevronRight className="h-4 w-4 ml-1" />
            مرحله قبل
          </Button>
        )}
        {step < 4 ? (
          <Button
            className="h-12 flex-[2] bg-emerald-600 hover:bg-emerald-700"
            onClick={next}
            disabled={!canNext(step)}
          >
            مرحله بعد
            <ChevronLeft className="h-4 w-4 mr-1" />
          </Button>
        ) : (
          <Button
            className="h-12 flex-[2] bg-emerald-600 hover:bg-emerald-700"
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending}
          >
            {submitMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 ml-1 animate-spin" />
                در حال ثبت…
              </>
            ) : (
              <>
                <CheckCircle2 className="h-5 w-5 ml-1" />
                ثبت نهایی فروش
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

function SalesTypeOption({
  value,
  label,
  description,
  active,
}: {
  value: string;
  label: string;
  description: string;
  active: boolean;
}) {
  return (
    <Label
      htmlFor={`sales-type-${value}`}
      className={cn(
        "cursor-pointer rounded-xl border p-3 transition-all block",
        active
          ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500/20"
          : "border-border bg-white hover:border-emerald-300"
      )}
    >
      <div className="flex items-center justify-between">
        <span className={cn("font-bold", active && "text-emerald-700")}>{label}</span>
        <RadioGroupItem value={value} id={`sales-type-${value}`} />
      </div>
      <p className="text-[11px] text-muted-foreground mt-0.5">{description}</p>
    </Label>
  );
}

function SummaryRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </span>
      <span className="text-xs font-medium text-right">{value}</span>
    </div>
  );
}
