"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { AlertTriangle, Boxes, Clock, Coins, FileBarChart, MapPin, TrendingUp, Truck } from "lucide-react";
import { api } from "@/lib/api";
import { formatNumber, formatRial, formatDate } from "@/lib/format";
import { TableSkeleton } from "@/components/common";
import { DateRangeFilter, DEFAULT_RANGE, rangeToQuery, type DateRangeValue } from "@/components/date-range-filter";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

// Shared date-range context — the toolbar at top of ReportsView sets it,
// and every tab consumes it via useReportsRange().
const ReportsRangeContext = React.createContext<{
  range: DateRangeValue;
  setRange: (v: DateRangeValue) => void;
}>({
  range: DEFAULT_RANGE,
  setRange: () => {},
});

function useReportsRange() {
  return React.useContext(ReportsRangeContext);
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StoreReceivableSale {
  sale_id: number;
  sale_no: string;
  sale_date: string;
  amount: string;
}
interface StoreReceivableRow {
  store_id: number;
  store_name: string;
  store_code: string;
  total_receivable: string;
  unsettled_count: number;
  sales: StoreReceivableSale[];
}
interface StoreReceivablesResponse {
  period_days: number;
  results: StoreReceivableRow[];
}

interface StoreStockRow {
  store_id: number;
  store_name: string;
  product_id: number;
  product_name: string;
  qty_on_hand: string;
  value: string;
}
interface StoreStockResponse {
  results: StoreStockRow[];
  totals: { total_qty: string; total_value: string };
}

interface DistributorStockRow {
  distributor_id: number;
  distributor_name: string;
  product_id: number;
  product_name: string;
  qty_delivered: string;
  qty_returned: string;
  qty_on_hand: string;
  value: string;
}
interface DistributorStockResponse {
  results: DistributorStockRow[];
}

interface DistributorCommissionRow {
  distributor_id: number;
  distributor_name: string;
  commission_rate: string;
  total_delivered_value: string;
  total_sold_value: string;
  total_returned_value: string;
  commission_owed: string;
}
interface DistributorCommissionResponse {
  period_days: number;
  results: DistributorCommissionRow[];
}

interface WasteDetailedByType {
  waste_type: string;
  waste_type_display: string;
  total_value: string;
  count: number;
}
interface WasteDetailedByProduct {
  product_id: number;
  product_name: string;
  total_qty: string;
  total_value: string;
}
interface WasteDetailedDetail {
  waste_no: string;
  waste_type: string;
  waste_type_display: string;
  location_name: string;
  waste_date: string;
  total_value: string;
  lines_count: number;
}
interface WasteDetailedResponse {
  period_days: number;
  total_value: string;
  by_type: WasteDetailedByType[];
  by_product: WasteDetailedByProduct[];
  details: WasteDetailedDetail[];
}

interface NearExpiryRow {
  lot_id: number;
  lot_no: string;
  product_id: number;
  product_name: string;
  expiry_date: string;
  days_remaining: number;
  qty_on_hand: string;
  warehouse_name: string;
}
interface NearExpiryResponse {
  days_threshold: number;
  today: string;
  count: number;
  results: NearExpiryRow[];
}

interface ProfitRow {
  key_id: number;
  key_name: string;
  total_amount: string;
  total_cost: string;
  total_profit: string;
  margin_pct: number;
  sale_count: number;
}
interface ProfitResponse {
  period_days: number;
  group_by: string;
  results: ProfitRow[];
  totals: {
    total_amount: string;
    total_cost: string;
    total_profit: string;
    margin_pct: number;
  };
}

// ---------------------------------------------------------------------------
// Shared toolbar
// ---------------------------------------------------------------------------

function DaysSelect({
  value,
  onChange,
  options = [7, 30, 90, 180],
}: {
  value: number;
  onChange: (v: number) => void;
  options?: number[];
}) {
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger className="w-40">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((d) => (
          <SelectItem key={d} value={String(d)}>{d} روز اخیر</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function ReportHeader({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <CardHeader className="flex-row items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </div>
      </div>
      {children}
    </CardHeader>
  );
}

function ErrorAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>خطا در بارگذاری</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}

function EmptyRow({ cols, label = "داده‌ای یافت نشد" }: { cols: number; label?: string }) {
  return (
    <TableRow>
      <TableCell colSpan={cols} className="text-center text-muted-foreground py-8">
        {label}
      </TableCell>
    </TableRow>
  );
}

function RangeChip({ range }: { range: DateRangeValue }) {
  return (
    <Badge variant="outline" className="font-mono nums text-[11px]" dir="ltr">
      {range.from ? formatDate(range.from) : "—"} ← {range.to ? formatDate(range.to) : "—"}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// 1) Store receivables
// ---------------------------------------------------------------------------

function StoreReceivablesTab() {
  const { range } = useReportsRange();
  const [expanded, setExpanded] = React.useState<number | null>(null);
  const { data, isLoading, error } = useQuery<StoreReceivablesResponse>({
    queryKey: ["report-store-receivables", range],
    queryFn: () => api<StoreReceivablesResponse>("/reports/store_receivables/", { query: { ...rangeToQuery(range) } }),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <ReportHeader
        icon={Coins}
        title="طلب از فروشگاه‌ها"
        description="مجموع مطالبات از فروشگاه‌ها همراه با جزئیات فروش تسویه‌نشده"
      >
        <RangeChip range={range} />
      </ReportHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">فروشگاه</TableHead>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">مجموع طلب (ریال)</TableHead>
                  <TableHead className="text-right">فروش‌های تسویه‌نشده</TableHead>
                  <TableHead className="text-right w-16">جزئیات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={5} className="p-0"><TableSkeleton rows={6} cols={5} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={5} />
                ) : (
                  rows.map((r) => (
                    <React.Fragment key={r.store_id}>
                      <TableRow>
                        <TableCell className="font-medium">{r.store_name}</TableCell>
                        <TableCell className="font-mono nums" dir="ltr">{r.store_code}</TableCell>
                        <TableCell className="nums font-semibold" dir="ltr">{formatRial(r.total_receivable)}</TableCell>
                        <TableCell className="nums" dir="ltr">{r.unsettled_count}</TableCell>
                        <TableCell>
                          <button
                            className="text-xs text-primary hover:underline"
                            onClick={() => setExpanded(expanded === r.store_id ? null : r.store_id)}
                          >
                            {expanded === r.store_id ? "بستن" : "نمایش"}
                          </button>
                        </TableCell>
                      </TableRow>
                      {expanded === r.store_id && (
                        <TableRow className="bg-muted/40">
                          <TableCell colSpan={5}>
                            <div className="overflow-x-auto scroll-pretty">
                              <Table>
                                <TableHeader>
                                  <TableRow>
                                    <TableHead className="text-right">شماره فروش</TableHead>
                                    <TableHead className="text-right">تاریخ</TableHead>
                                    <TableHead className="text-right">مبلغ</TableHead>
                                  </TableRow>
                                </TableHeader>
                                <TableBody>
                                  {r.sales.length === 0 ? (
                                    <EmptyRow cols={3} />
                                  ) : (
                                    r.sales.map((s) => (
                                      <TableRow key={s.sale_id}>
                                        <TableCell className="font-mono nums" dir="ltr">{s.sale_no}</TableCell>
                                        <TableCell className="nums" dir="ltr">{formatDate(s.sale_date)}</TableCell>
                                        <TableCell className="nums" dir="ltr">{formatRial(s.amount)}</TableCell>
                                      </TableRow>
                                    ))
                                  )}
                                </TableBody>
                              </Table>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
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
// 2) Store stock
// ---------------------------------------------------------------------------

function StoreStockTab() {
  const { data, isLoading, error } = useQuery<StoreStockResponse>({
    queryKey: ["report-store-stock"],
    queryFn: () => api<StoreStockResponse>("/reports/store_stock/"),
  });
  const rows = data?.results ?? [];
  const totals = data?.totals;
  return (
    <Card>
      <ReportHeader
        icon={Boxes}
        title="کالای نزد فروشگاه"
        description="موجودی کالاهای امانی نزد هر فروشگاه به تفکیک محصول"
      />
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">فروشگاه</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">ارزش (ریال)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={4} className="p-0"><TableSkeleton rows={8} cols={4} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={4} />
                ) : (
                  rows.map((r, i) => (
                    <TableRow key={`${r.store_id}-${r.product_id}-${i}`}>
                      <TableCell className="font-medium">{r.store_name}</TableCell>
                      <TableCell>{r.product_name}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(r.qty_on_hand)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(r.value)}</TableCell>
                    </TableRow>
                  ))
                )}
                {totals && !isLoading && (
                  <TableRow className="bg-muted/40 font-semibold">
                    <TableCell colSpan={2}>جمع کل</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(totals.total_qty)}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatRial(totals.total_value)}</TableCell>
                  </TableRow>
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
// 3) Distributor stock
// ---------------------------------------------------------------------------

function DistributorStockTab() {
  const { data, isLoading, error } = useQuery<DistributorStockResponse>({
    queryKey: ["report-distributor-stock"],
    queryFn: () => api<DistributorStockResponse>("/reports/distributor_stock/"),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <ReportHeader
        icon={Truck}
        title="کالای نزد عامل پخش"
        description="موجودی کالاهای تحویلی به عوامل پخش به تفکیک محصول"
      />
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">عامل پخش</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">تحویلی</TableHead>
                  <TableHead className="text-right">برگشتی</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">ارزش (ریال)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={8} cols={6} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={6} />
                ) : (
                  rows.map((r, i) => (
                    <TableRow key={`${r.distributor_id}-${r.product_id}-${i}`}>
                      <TableCell className="font-medium">{r.distributor_name}</TableCell>
                      <TableCell>{r.product_name}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(r.qty_delivered)}</TableCell>
                      <TableCell className="nums text-muted-foreground" dir="ltr">{formatNumber(r.qty_returned)}</TableCell>
                      <TableCell className="nums font-semibold" dir="ltr">{formatNumber(r.qty_on_hand)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(r.value)}</TableCell>
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
// 4) Distributor commission
// ---------------------------------------------------------------------------

function DistributorCommissionTab() {
  const { range } = useReportsRange();
  const { data, isLoading, error } = useQuery<DistributorCommissionResponse>({
    queryKey: ["report-distributor-commission", range],
    queryFn: () => api<DistributorCommissionResponse>("/reports/distributor_commission/", { query: { ...rangeToQuery(range) } }),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <ReportHeader
        icon={Coins}
        title="دستمزد عوامل پخش"
        description="محاسبه دستمزد پورسانتی بر اساس فروش و نرخ هر عامل"
      >
        <RangeChip range={range} />
      </ReportHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">عامل پخش</TableHead>
                  <TableHead className="text-right">نرخ</TableHead>
                  <TableHead className="text-right">تحویلی</TableHead>
                  <TableHead className="text-right">فروخته‌شده</TableHead>
                  <TableHead className="text-right">برگشتی</TableHead>
                  <TableHead className="text-right">دستمزد قابل پرداخت</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={5} cols={6} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={6} />
                ) : (
                  rows.map((r) => (
                    <TableRow key={r.distributor_id}>
                      <TableCell className="font-medium">{r.distributor_name}</TableCell>
                      <TableCell className="nums" dir="ltr">{r.commission_rate}%</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(r.total_delivered_value)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(r.total_sold_value)}</TableCell>
                      <TableCell className="nums text-muted-foreground" dir="ltr">{formatRial(r.total_returned_value)}</TableCell>
                      <TableCell className="nums font-semibold text-emerald-600 dark:text-emerald-400" dir="ltr">{formatRial(r.commission_owed)}</TableCell>
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
// 5) Waste detailed
// ---------------------------------------------------------------------------

function WasteDetailedTab() {
  const { range } = useReportsRange();
  const { data, isLoading, error } = useQuery<WasteDetailedResponse>({
    queryKey: ["report-waste-detailed", range],
    queryFn: () => api<WasteDetailedResponse>("/reports/waste_report_detailed/", { query: { ...rangeToQuery(range) } }),
  });
  return (
    <div className="space-y-4">
      <Card>
        <ReportHeader
          icon={AlertTriangle}
          title="گزارش ضایعات"
          description="تحلیل ضایعات بر اساس نوع، محصول و سند"
        >
          <RangeChip range={range} />
        </ReportHeader>
        <CardContent>
          {error ? (
            <ErrorAlert message={(error as Error).message} />
          ) : isLoading ? (
            <TableSkeleton rows={3} cols={3} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">ارزش کل ضایعات</p>
                <p className="text-xl font-bold nums">{formatRial(data?.total_value ?? "0")}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">تعداد اسناد</p>
                <p className="text-xl font-bold nums">{data?.details.length ?? 0}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-xs text-muted-foreground">دوره گزارش</p>
                <p className="text-xl font-bold nums">{data?.period_days ?? "—"} روز</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <ReportHeader icon={Boxes} title="تفکیک بر اساس نوع" description="هزینه ضایعات به تفکیک محل وقوع" />
        <CardContent className="p-0">
          {error ? (
            <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
          ) : (
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">نوع</TableHead>
                    <TableHead className="text-right">تعداد</TableHead>
                    <TableHead className="text-right">ارزش (ریال)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={3} className="p-0"><TableSkeleton rows={3} cols={3} /></TableCell></TableRow>
                  ) : (data?.by_type ?? []).length === 0 ? (
                    <EmptyRow cols={3} />
                  ) : (
                    (data?.by_type ?? []).map((t) => (
                      <TableRow key={t.waste_type}>
                        <TableCell className="font-medium">{t.waste_type_display ?? t.waste_type}</TableCell>
                        <TableCell className="nums" dir="ltr">{t.count}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(t.total_value)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <ReportHeader icon={Boxes} title="تفکیک بر اساس محصول" description="مقدار و ارزش ضایعات به تفکیک محصول" />
        <CardContent className="p-0">
          {error ? (
            <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
          ) : (
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                    <TableHead className="text-right">ارزش (ریال)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={3} className="p-0"><TableSkeleton rows={4} cols={3} /></TableCell></TableRow>
                  ) : (data?.by_product ?? []).length === 0 ? (
                    <EmptyRow cols={3} />
                  ) : (
                    (data?.by_product ?? []).map((p) => (
                      <TableRow key={p.product_id}>
                        <TableCell className="font-medium">{p.product_name}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(p.total_qty)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(p.total_value)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <ReportHeader icon={FileBarChart} title="اسناد ضایعات" description="لیست اسناد ضایعات ثبت‌شده در دوره" />
        <CardContent className="p-0">
          {error ? (
            <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
          ) : (
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">شماره</TableHead>
                    <TableHead className="text-right">نوع</TableHead>
                    <TableHead className="text-right">محل</TableHead>
                    <TableHead className="text-right">تعداد خطوط</TableHead>
                    <TableHead className="text-right">ارزش (ریال)</TableHead>
                    <TableHead className="text-right">تاریخ</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={6} cols={6} /></TableCell></TableRow>
                  ) : (data?.details ?? []).length === 0 ? (
                    <EmptyRow cols={6} />
                  ) : (
                    (data?.details ?? []).map((d) => (
                      <TableRow key={d.waste_no}>
                        <TableCell className="font-mono nums" dir="ltr">{d.waste_no}</TableCell>
                        <TableCell><Badge variant="secondary">{d.waste_type_display ?? d.waste_type}</Badge></TableCell>
                        <TableCell>{d.location_name || "—"}</TableCell>
                        <TableCell className="nums" dir="ltr">{d.lines_count}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(d.total_value)}</TableCell>
                        <TableCell className="text-xs text-muted-foreground nums" dir="ltr">{formatDate(d.waste_date)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 6) Near expiry
// ---------------------------------------------------------------------------

function NearExpiryTab() {
  const [days, setDays] = React.useState(7);
  const { data, isLoading, error } = useQuery<NearExpiryResponse>({
    queryKey: ["report-near-expiry", days],
    queryFn: () => api<NearExpiryResponse>("/reports/near_expiry/", { query: { days_threshold: days } }),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <ReportHeader
        icon={Clock}
        title="کالای نزدیک انقضا"
        description="لات‌هایی که در آستانه انقضا هستند (با پایش دستی)"
      >
        <DaysSelect value={days} onChange={setDays} options={[3, 7, 14, 30]} />
      </ReportHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">لات</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">انبار</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">تاریخ انقضا</TableHead>
                  <TableHead className="text-right">روزهای باقیمانده</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={8} cols={6} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={6} label="لات نزدیک انقضایی یافت نشد" />
                ) : (
                  rows.map((r) => {
                    const danger = r.days_remaining <= 3;
                    return (
                      <TableRow key={r.lot_id} className={danger ? "bg-rose-50 dark:bg-rose-950/30" : ""}>
                        <TableCell className="font-mono nums" dir="ltr">{r.lot_no}</TableCell>
                        <TableCell className="font-medium">{r.product_name}</TableCell>
                        <TableCell>{r.warehouse_name ?? "—"}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(r.qty_on_hand)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatDate(r.expiry_date)}</TableCell>
                        <TableCell>
                          <Badge variant={danger ? "destructive" : "secondary"} className="nums">
                            {r.days_remaining} روز
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })
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
// 7) Profit report
// ---------------------------------------------------------------------------

function ProfitTab() {
  const { range } = useReportsRange();
  const [groupBy, setGroupBy] = React.useState<"product" | "store" | "distributor">("product");
  const { data, isLoading, error } = useQuery<ProfitResponse>({
    queryKey: ["report-profit", range, groupBy],
    queryFn: () => api<ProfitResponse>("/reports/profit_report/", { query: { group_by: groupBy, ...rangeToQuery(range) } }),
  });
  const rows = data?.results ?? [];
  const totals = data?.totals;
  return (
    <Card>
      <ReportHeader
        icon={TrendingUp}
        title="گزارش سود"
        description="سود و حاشیه به تفکیک محصول/فروشگاه/عامل پخش"
      >
        <div className="flex items-center gap-2">
          <Select value={groupBy} onValueChange={(v) => setGroupBy(v as "product" | "store" | "distributor")}>
            <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="product">محصول</SelectItem>
              <SelectItem value="store">فروشگاه</SelectItem>
              <SelectItem value="distributor">عامل پخش</SelectItem>
            </SelectContent>
          </Select>
          <RangeChip range={range} />
        </div>
      </ReportHeader>
      <CardContent className="p-0">
        {error ? (
          <div className="p-4"><ErrorAlert message={(error as Error).message} /></div>
        ) : (
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">نام</TableHead>
                  <TableHead className="text-right">فروش (ریال)</TableHead>
                  <TableHead className="text-right">بهای تمام‌شده</TableHead>
                  <TableHead className="text-right">سود</TableHead>
                  <TableHead className="text-right">حاشیه</TableHead>
                  <TableHead className="text-right">تعداد فروش</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={6} cols={6} /></TableCell></TableRow>
                ) : rows.length === 0 ? (
                  <EmptyRow cols={6} />
                ) : (
                  rows.map((r) => (
                    <TableRow key={r.key_id}>
                      <TableCell className="font-medium">{r.key_name}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(r.total_amount)}</TableCell>
                      <TableCell className="nums text-muted-foreground" dir="ltr">{formatRial(r.total_cost)}</TableCell>
                      <TableCell className="nums font-semibold text-emerald-600 dark:text-emerald-400" dir="ltr">{formatRial(r.total_profit)}</TableCell>
                      <TableCell className="nums" dir="ltr">{r.margin_pct}%</TableCell>
                      <TableCell className="nums" dir="ltr">{r.sale_count}</TableCell>
                    </TableRow>
                  ))
                )}
                {totals && !isLoading && (
                  <TableRow className="bg-muted/40 font-semibold">
                    <TableCell>جمع کل</TableCell>
                    <TableCell className="nums" dir="ltr">{formatRial(totals.total_amount)}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatRial(totals.total_cost)}</TableCell>
                    <TableCell className="nums text-emerald-600 dark:text-emerald-400" dir="ltr">{formatRial(totals.total_profit)}</TableCell>
                    <TableCell className="nums" dir="ltr">{totals.margin_pct}%</TableCell>
                    <TableCell>—</TableCell>
                  </TableRow>
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
// Main
// ---------------------------------------------------------------------------

export function ReportsView() {
  // Silence unused import warning in case toast is removed in the future.
  void toast;
  void MapPin;
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);
  return (
    <ReportsRangeContext.Provider value={{ range, setRange }}>
      <div className="space-y-4">
        {/* Shared date-range toolbar — applies to all 7 tabs */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base"><FileBarChart className="h-5 w-5" /> بازه‌ی گزارش</CardTitle>
            <CardDescription>این فیلتر روی همه‌ی تب‌های گزارش اعمال می‌شود</CardDescription>
          </CardHeader>
          <CardContent>
            <DateRangeFilter value={range} onChange={setRange} />
          </CardContent>
        </Card>
        <Tabs defaultValue="store-receivables">
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="store-receivables"><Coins className="h-4 w-4" /> طلب از فروشگاه‌ها</TabsTrigger>
            <TabsTrigger value="store-stock"><Boxes className="h-4 w-4" /> کالای نزد فروشگاه</TabsTrigger>
            <TabsTrigger value="distributor-stock"><Truck className="h-4 w-4" /> کالای نزد عامل پخش</TabsTrigger>
            <TabsTrigger value="distributor-commission"><Coins className="h-4 w-4" /> دستمزد عوامل پخش</TabsTrigger>
            <TabsTrigger value="waste-detailed"><AlertTriangle className="h-4 w-4" /> گزارش ضایعات</TabsTrigger>
            <TabsTrigger value="near-expiry"><Clock className="h-4 w-4" /> کالای نزدیک انقضا</TabsTrigger>
            <TabsTrigger value="profit"><TrendingUp className="h-4 w-4" /> گزارش سود</TabsTrigger>
          </TabsList>
          <TabsContent value="store-receivables" className="mt-4"><StoreReceivablesTab /></TabsContent>
          <TabsContent value="store-stock" className="mt-4"><StoreStockTab /></TabsContent>
          <TabsContent value="distributor-stock" className="mt-4"><DistributorStockTab /></TabsContent>
          <TabsContent value="distributor-commission" className="mt-4"><DistributorCommissionTab /></TabsContent>
          <TabsContent value="waste-detailed" className="mt-4"><WasteDetailedTab /></TabsContent>
          <TabsContent value="near-expiry" className="mt-4"><NearExpiryTab /></TabsContent>
          <TabsContent value="profit" className="mt-4"><ProfitTab /></TabsContent>
        </Tabs>
      </div>
    </ReportsRangeContext.Provider>
  );
}
