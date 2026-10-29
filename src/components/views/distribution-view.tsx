"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import {
  AlertTriangle,
  Coins,
  FileBarChart,
  ListOrdered,
  Plus,
  Save,
  Trash2,
  Truck,
} from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import {
  MOCK_DISTRIBUTORS,
  MOCK_PRODUCTS,
  MOCK_STORES,
} from "@/lib/mock-data";
import { formatDate, formatNumber, formatRial } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState, TableSkeleton } from "@/components/common";
import {
  DateRangeFilter,
  DEFAULT_RANGE,
  rangeToQuery,
  type DateRangeValue,
} from "@/components/date-range-filter";
import { DatePicker } from "@/components/dialogs/datepicker";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Distributor = (typeof MOCK_DISTRIBUTORS)[number];
type Product = (typeof MOCK_PRODUCTS)[number];
type Store = (typeof MOCK_STORES)[number];

interface SettlementCheckResponse {
  distributor_id: number;
  has_unsettled: boolean;
  unsettled_count: number;
  warning: string | null;
}

interface SummaryRow {
  distributor_id: number;
  distributor_code: string;
  distributor_name: string;
  total_delivered_value: string;
  total_sold_value: string;
  total_to_stores_value: string;
  total_returned_value: string;
  balance: string;
  commission_rate: string;
  commission_owed: string;
  store_count: number;
}
interface SummaryResponse {
  start_date: string | null;
  end_date: string | null;
  results: SummaryRow[];
  totals: {
    total_delivered_value: string;
    total_sold_value: string;
    total_to_stores_value: string;
    total_returned_value: string;
    balance: string;
    commission_owed: string;
  };
}

interface DetailRow {
  distributor_id: number;
  distributor_name: string;
  product_id: number;
  product_name: string;
  product_code: string;
  qty_delivered: string;
  qty_sold: string;
  qty_to_stores: string;
  qty_returned: string;
  qty_balance: string;
}
interface DetailResponse {
  start_date: string | null;
  end_date: string | null;
  results: DetailRow[];
}

interface CommissionRow {
  distributor_id: number;
  distributor_code: string;
  distributor_name: string;
  total_sales: string;
  commission_rate: string;
  commission_amount: string;
  settlement_status: "settled" | "unsettled";
  basis: string;
}
interface CommissionResponse {
  start_date: string | null;
  end_date: string | null;
  basis: string;
  results: CommissionRow[];
  totals: {
    total_sales: string;
    commission_amount: string;
  };
}

// ---------------------------------------------------------------------------
// Tab 1 — تحویل جدید
// ---------------------------------------------------------------------------

interface NewDispatchLine {
  product_id: string;
  qty: string;
  unit_price: string;
  dest_store_id: string;
}

function NewDispatchTab() {
  const qc = useQueryClient();
  const [distributorId, setDistributorId] = React.useState("");
  const [dispatchDate, setDispatchDate] = React.useState<string | null>(
    new Date().toISOString().slice(0, 10),
  );
  const [notes, setNotes] = React.useState("");
  const [lines, setLines] = React.useState<NewDispatchLine[]>([
    { product_id: "", qty: "1", unit_price: "0", dest_store_id: "" },
  ]);

  const { data: distributorsData } = useQuery({
    queryKey: ["distributors-list-d02"],
    queryFn: () =>
      api<Paginated<Distributor>>("/partners/distributors/", {
        query: { page: 1, page_size: 100 },
      }),
  });
  const { data: productsData } = useQuery({
    queryKey: ["products-list-d02"],
    queryFn: () =>
      api<Paginated<Product>>("/products/", {
        query: { page: 1, page_size: 100, is_finished_good: true },
      }),
  });
  const { data: storesData } = useQuery({
    queryKey: ["stores-list-d02"],
    queryFn: () =>
      api<Paginated<Store>>("/partners/stores/", {
        query: { page: 1, page_size: 100 },
      }),
  });

  const distributors = distributorsData?.results ?? [];
  const products = productsData?.results ?? [];
  const stores = storesData?.results ?? [];

  // Settlement check
  const {
    data: settlement,
    isLoading: settlementLoading,
  } = useQuery<SettlementCheckResponse>({
    queryKey: ["settlement-check", distributorId],
    queryFn: () =>
      api<SettlementCheckResponse>("/dispatch/settlement_check/", {
        query: { distributor_id: distributorId },
      }),
    enabled: !!distributorId,
  });

  const addLine = () =>
    setLines((l) => [
      ...l,
      { product_id: "", qty: "1", unit_price: "0", dest_store_id: "" },
    ]);
  const removeLine = (i: number) =>
    setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<NewDispatchLine>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const totalQty = lines.reduce(
    (s, l) => s + (parseFloat(l.qty) || 0),
    0,
  );
  const totalAmount = lines.reduce(
    (s, l) => s + (parseFloat(l.qty) || 0) * (parseFloat(l.unit_price) || 0),
    0,
  );

  const mutation = useMutation({
    mutationFn: () => {
      if (!distributorId) throw new Error("عامل پخش را انتخاب کنید.");
      if (lines.length === 0) throw new Error("حداقل یک ردیف لازم است.");
      const invalid = lines.find(
        (l) =>
          !l.product_id || !l.qty || !l.unit_price || !l.dest_store_id,
      );
      if (invalid) throw new Error("همه‌ی فیلدهای ردیف‌ها را تکمیل کنید.");
      return api("/dispatch/create/", {
        method: "POST",
        body: {
          distributor_id: Number(distributorId),
          dispatch_date: dispatchDate,
          notes,
          lines: lines.map((l) => ({
            product_id: Number(l.product_id),
            qty: l.qty,
            unit_price: l.unit_price,
            dest_store_id: Number(l.dest_store_id),
          })),
        },
      });
    },
    onSuccess: () => {
      toast.success("سند پخش جدید با موفقیت ثبت شد.");
      qc.invalidateQueries({ queryKey: ["dispatches"] });
      qc.invalidateQueries({ queryKey: ["settlement-check", distributorId] });
      setDistributorId("");
      setNotes("");
      setLines([
        { product_id: "", qty: "1", unit_price: "0", dest_store_id: "" },
      ]);
    },
    onError: (e: Error) => {
      const msg =
        e && typeof e === "object" && "detail" in e
          ? (() => {
              const d = (e as { detail: unknown }).detail;
              if (typeof d === "string") return d;
              try {
                return JSON.stringify(d);
              } catch {
                return e.message;
              }
            })()
          : e.message;
      toast.error(`خطا در ثبت: ${msg}`);
    },
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Truck className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base">تحویل جدید به عامل پخش</CardTitle>
            <CardDescription>
              ثبت سند پخش جدید و انتقال خودکار موجودی به انبار مجازی عامل
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* header fields */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <Label>عامل پخش</Label>
            <Select value={distributorId} onValueChange={setDistributorId}>
              <SelectTrigger>
                <SelectValue placeholder="انتخاب عامل پخش" />
              </SelectTrigger>
              <SelectContent>
                {distributors.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.code} — {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>تاریخ تحویل</Label>
            <DatePicker
              value={dispatchDate}
              onChange={setDispatchDate}
              placeholder="انتخاب تاریخ"
            />
          </div>
          <div className="space-y-1.5">
            <Label>تعداد فروشگاه‌ها</Label>
            <Input
              value={String(stores.length)}
              disabled
              className="bg-muted/40"
            />
          </div>
        </div>

        {/* Settlement check warning */}
        {distributorId && (
          <div>
            {settlementLoading ? (
              <p className="text-xs text-muted-foreground">
                در حال بررسی وضعیت تسویه…
              </p>
            ) : settlement?.has_unsettled ? (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>هشدار: تحویل تسویه‌نشده</AlertTitle>
                <AlertDescription>
                  {settlement.warning} (تعداد: {settlement.unsettled_count})
                </AlertDescription>
              </Alert>
            ) : settlement ? (
              <Alert>
                <Coins className="h-4 w-4" />
                <AlertTitle>وضعیت تسویه: بدون مشکل</AlertTitle>
                <AlertDescription>
                  این عامل پخش تحویل تسویه‌نشده ندارد.
                </AlertDescription>
              </Alert>
            ) : null}
          </div>
        )}

        {/* Lines table */}
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right w-12">ردیف</TableHead>
                <TableHead className="text-right">محصول</TableHead>
                <TableHead className="text-right w-28">تعداد</TableHead>
                <TableHead className="text-right w-36">قیمت فروش</TableHead>
                <TableHead className="text-right w-32">قیمت کل</TableHead>
                <TableHead className="text-right">فروشگاه مقصد</TableHead>
                <TableHead className="text-right w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lines.map((l, i) => {
                const lineTotal =
                  (parseFloat(l.qty) || 0) * (parseFloat(l.unit_price) || 0);
                return (
                  <TableRow key={i}>
                    <TableCell className="text-muted-foreground nums">
                      {i + 1}
                    </TableCell>
                    <TableCell>
                      <Select
                        value={l.product_id}
                        onValueChange={(v) => {
                          const p = products.find((x) => String(x.id) === v);
                          updateLine(i, {
                            product_id: v,
                            unit_price: p
                              ? String(parseFloat(p.default_price))
                              : l.unit_price,
                          });
                        }}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="انتخاب محصول" />
                        </SelectTrigger>
                        <SelectContent>
                          {products.map((p) => (
                            <SelectItem key={p.id} value={String(p.id)}>
                              {p.code} — {p.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={l.qty}
                        onChange={(e) =>
                          updateLine(i, { qty: e.target.value })
                        }
                        className="text-right nums"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        value={l.unit_price}
                        onChange={(e) =>
                          updateLine(i, { unit_price: e.target.value })
                        }
                        className="text-right nums"
                      />
                    </TableCell>
                    <TableCell className="nums font-medium" dir="ltr">
                      {formatRial(lineTotal)}
                    </TableCell>
                    <TableCell>
                      <Select
                        value={l.dest_store_id}
                        onValueChange={(v) =>
                          updateLine(i, { dest_store_id: v })
                        }
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="فروشگاه مقصد" />
                        </SelectTrigger>
                        <SelectContent>
                          {stores.map((s) => (
                            <SelectItem key={s.id} value={String(s.id)}>
                              {s.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="حذف ردیف"
                        disabled={lines.length === 1}
                        onClick={() => removeLine(i)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>

        {/* Notes + totals + actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="dispatch-notes">یادداشت</Label>
            <Input
              id="dispatch-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="توضیحات اختیاری"
            />
          </div>
          <div className="space-y-1.5">
            <Label>مجموع کل</Label>
            <div className="rounded-lg border bg-muted/40 px-3 py-2 nums text-sm font-semibold" dir="ltr">
              {formatRial(totalAmount)}
              <span className="text-muted-foreground mx-2">|</span>
              {formatNumber(totalQty)} عدد
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 pt-2 border-t">
          <Button variant="outline" onClick={addLine}>
            <Plus className="h-4 w-4 ml-1" />
            افزودن ردیف
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              mutation.isPending ||
              !distributorId ||
              lines.length === 0
            }
          >
            <Save className="h-4 w-4 ml-1" />
            {mutation.isPending ? "در حال ثبت…" : "ثبت سند پخش"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Tab 2 — گزارش کلی
// ---------------------------------------------------------------------------

function SummaryTab({ range }: { range: DateRangeValue }) {
  const { data, isLoading, error } = useQuery<SummaryResponse>({
    queryKey: ["distribution-summary", range],
    queryFn: () =>
      api<SummaryResponse>("/dispatch/distributor_summary/", {
        query: { ...rangeToQuery(range) },
      }),
  });

  const rows = data?.results ?? [];
  const totals = data?.totals;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <ListOrdered className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base">گزارش کلی عوامل پخش</CardTitle>
            <CardDescription>
              جمع تحویلی، فروش، تحویل به فروشگاه‌ها، مانده و پورسانت هر عامل
            </CardDescription>
          </div>
        </div>
        <Badge variant="outline" className="font-mono nums text-[11px]" dir="ltr">
          {range.from ? formatDate(range.from) : "—"} ← {range.to ? formatDate(range.to) : "—"}
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>خطا در بارگذاری</AlertTitle>
              <AlertDescription>{(error as Error).message}</AlertDescription>
            </Alert>
          </div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">عامل پخش</TableHead>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">مبلغ تحویلی</TableHead>
                  <TableHead className="text-right">مبلغ فروخته‌شده</TableHead>
                  <TableHead className="text-right">تحویل به فروشگاه</TableHead>
                  <TableHead className="text-right">مانده</TableHead>
                  <TableHead className="text-right">پورسانت</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="p-0">
                      <TableSkeleton rows={6} cols={7} />
                    </TableCell>
                  </TableRow>
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <EmptyState title="داده‌ای یافت نشد" />
                    </TableCell>
                  </TableRow>
                ) : (
                  <>
                    {rows.map((r) => (
                      <TableRow key={r.distributor_id}>
                        <TableCell className="font-medium">
                          {r.distributor_name}
                        </TableCell>
                        <TableCell className="font-mono nums" dir="ltr">
                          {r.distributor_code}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(r.total_delivered_value)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(r.total_sold_value)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(r.total_to_stores_value)}
                        </TableCell>
                        <TableCell
                          className={`nums ${parseFloat(r.balance) < 0 ? "text-destructive" : "text-emerald-600"} font-semibold`}
                          dir="ltr"
                        >
                          {formatRial(r.balance)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          <div className="flex flex-col leading-tight">
                            <span className="font-semibold">
                              {formatRial(r.commission_owed)}
                            </span>
                            <span className="text-[10px] text-muted-foreground">
                              {formatNumber(r.commission_rate)}٪
                            </span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                    {totals && (
                      <TableRow className="bg-muted/40 font-semibold border-t-2">
                        <TableCell>جمع کل</TableCell>
                        <TableCell />
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.total_delivered_value)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.total_sold_value)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.total_to_stores_value)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.balance)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.commission_owed)}
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Tab 3 — گزارش تفصیلی
// ---------------------------------------------------------------------------

function DetailTab({ range }: { range: DateRangeValue }) {
  const { data, isLoading, error } = useQuery<DetailResponse>({
    queryKey: ["distribution-detail", range],
    queryFn: () =>
      api<DetailResponse>("/dispatch/distributor_detail/", {
        query: { ...rangeToQuery(range) },
      }),
  });

  const rows = data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <FileBarChart className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base">گزارش تفصیلی عوامل پخش</CardTitle>
            <CardDescription>
              جزئیات تحویل، فروش و مانده به تفکیک عامل × محصول
            </CardDescription>
          </div>
        </div>
        <Badge variant="outline" className="font-mono nums text-[11px]" dir="ltr">
          {range.from ? formatDate(range.from) : "—"} ← {range.to ? formatDate(range.to) : "—"}
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>خطا در بارگذاری</AlertTitle>
              <AlertDescription>{(error as Error).message}</AlertDescription>
            </Alert>
          </div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">عامل پخش</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">کد محصول</TableHead>
                  <TableHead className="text-right">تحویل گرفته</TableHead>
                  <TableHead className="text-right">فروخته‌شده</TableHead>
                  <TableHead className="text-right">تحویل به فروشگاه</TableHead>
                  <TableHead className="text-right">مانده</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="p-0">
                      <TableSkeleton rows={8} cols={7} />
                    </TableCell>
                  </TableRow>
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <EmptyState title="داده‌ای یافت نشد" />
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((r, i) => (
                    <TableRow key={`${r.distributor_id}-${r.product_id}-${i}`}>
                      <TableCell className="font-medium">
                        {r.distributor_name}
                      </TableCell>
                      <TableCell>{r.product_name}</TableCell>
                      <TableCell className="font-mono nums" dir="ltr">
                        {r.product_code || "—"}
                      </TableCell>
                      <TableCell className="nums" dir="ltr">
                        {formatNumber(r.qty_delivered)}
                      </TableCell>
                      <TableCell className="nums" dir="ltr">
                        {formatNumber(r.qty_sold)}
                      </TableCell>
                      <TableCell className="nums" dir="ltr">
                        {formatNumber(r.qty_to_stores)}
                      </TableCell>
                      <TableCell
                        className={`nums font-semibold ${parseFloat(r.qty_balance) < 0 ? "text-destructive" : ""}`}
                        dir="ltr"
                      >
                        {formatNumber(r.qty_balance)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Tab 4 — گزارش پورسانت
// ---------------------------------------------------------------------------

function CommissionTab({ range }: { range: DateRangeValue }) {
  const [basis, setBasis] = React.useState<"total" | "settled">("total");

  const { data, isLoading, error } = useQuery<CommissionResponse>({
    queryKey: ["distribution-commission", range, basis],
    queryFn: () =>
      api<CommissionResponse>("/dispatch/distributor_commission/", {
        query: { ...rangeToQuery(range), basis },
      }),
  });

  const rows = data?.results ?? [];
  const totals = data?.totals;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Coins className="h-5 w-5" />
          </div>
          <div>
            <CardTitle className="text-base">گزارش پورسانت عوامل پخش</CardTitle>
            <CardDescription>
              جمع فروش و محاسبه پورسانت بر اساس درصد هر عامل
            </CardDescription>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={basis}
            onValueChange={(v) => setBasis(v as "total" | "settled")}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="total">کل فروش</SelectItem>
              <SelectItem value="settled">فروش تسویه‌شده</SelectItem>
            </SelectContent>
          </Select>
          <Badge variant="outline" className="font-mono nums text-[11px]" dir="ltr">
            {range.from ? formatDate(range.from) : "—"} ← {range.to ? formatDate(range.to) : "—"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>خطا در بارگذاری</AlertTitle>
              <AlertDescription>{(error as Error).message}</AlertDescription>
            </Alert>
          </div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">عامل پخش</TableHead>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">فروش کل</TableHead>
                  <TableHead className="text-right">درصد پورسانت</TableHead>
                  <TableHead className="text-right">مبلغ پورسانت</TableHead>
                  <TableHead className="text-right">وضعیت تسویه</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="p-0">
                      <TableSkeleton rows={5} cols={6} />
                    </TableCell>
                  </TableRow>
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <EmptyState title="داده‌ای یافت نشد" />
                    </TableCell>
                  </TableRow>
                ) : (
                  <>
                    {rows.map((r) => (
                      <TableRow key={r.distributor_id}>
                        <TableCell className="font-medium">
                          {r.distributor_name}
                        </TableCell>
                        <TableCell className="font-mono nums" dir="ltr">
                          {r.distributor_code}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatRial(r.total_sales)}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          {formatNumber(r.commission_rate)}٪
                        </TableCell>
                        <TableCell className="nums font-semibold" dir="ltr">
                          {formatRial(r.commission_amount)}
                        </TableCell>
                        <TableCell>
                          {r.settlement_status === "settled" ? (
                            <Badge className="border-transparent bg-emerald-600 text-white hover:bg-emerald-600/90">
                              تسویه‌شده
                            </Badge>
                          ) : (
                            <Badge variant="destructive">تسویه‌نشده</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                    {totals && (
                      <TableRow className="bg-muted/40 font-semibold border-t-2">
                        <TableCell>جمع کل</TableCell>
                        <TableCell />
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.total_sales)}
                        </TableCell>
                        <TableCell />
                        <TableCell className="nums" dir="ltr">
                          {formatRial(totals.commission_amount)}
                        </TableCell>
                        <TableCell />
                      </TableRow>
                    )}
                  </>
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

export function DistributionView() {
  const [tab, setTab] = React.useState("new");
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);

  return (
    <div className="space-y-4" dir="rtl">
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="new">تحویل جدید</TabsTrigger>
          <TabsTrigger value="summary">گزارش کلی</TabsTrigger>
          <TabsTrigger value="detail">گزارش تفصیلی</TabsTrigger>
          <TabsTrigger value="commission">گزارش پورسانت</TabsTrigger>
        </TabsList>

        <TabsContent value="new" className="mt-4">
          <NewDispatchTab />
        </TabsContent>

        <TabsContent value="summary" className="mt-4 space-y-4">
          <DateRangeFilter value={range} onChange={setRange} />
          <SummaryTab range={range} />
        </TabsContent>

        <TabsContent value="detail" className="mt-4 space-y-4">
          <DateRangeFilter value={range} onChange={setRange} />
          <DetailTab range={range} />
        </TabsContent>

        <TabsContent value="commission" className="mt-4 space-y-4">
          <DateRangeFilter value={range} onChange={setRange} />
          <CommissionTab range={range} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
