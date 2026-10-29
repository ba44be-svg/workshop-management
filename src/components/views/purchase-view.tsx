"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, ShoppingCart, FileText, X, Undo2, Search } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { MOCK_PURCHASES, MOCK_PURCHASE_RETURNS } from "@/lib/mock-data";
import { formatNumber, formatRial, formatDate } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pager, TableSkeleton, EmptyState } from "@/components/common";
import { PurchaseDialog } from "@/components/dialogs/purchase-dialog";
import { PurchaseReturnDialog } from "@/components/dialogs/purchase-return-dialog";
import { DateRangeFilter, DEFAULT_RANGE, rangeToQuery, type DateRangeValue } from "@/components/date-range-filter";

type Purchase = (typeof MOCK_PURCHASES)[number] & {
  lines?: Array<{
    product: number;
    product_name: string;
    qty: string;
    unit_price: string;
    unit_id?: number | null;
    shelf_life_days: number;
    expiry_date: string;
    lot_no: string;
    line_total?: string;
    returned_qty?: string; // مقدار برگشتی این قلم
  }>;
  cash_account?: number | null;
  cash_account_name?: string;
  journal?: number | null;
  journal_no?: string;
  created_at?: string;
  has_returns?: boolean; // آیا این فاکتور برگشتی دارد
};

type PurchaseReturn = (typeof MOCK_PURCHASE_RETURNS)[number];

interface StatCardProps {
  label: string;
  value: string | number;
  loading?: boolean;
  tone?: string;
}

function StatCard({ label, value, loading, tone = "bg-primary/10 text-primary" }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-[11px] text-muted-foreground">{label}</p>
        {loading ? (
          <Skeleton className="mt-2 h-6 w-20" />
        ) : (
          <p className="mt-1 text-lg font-bold nums">{value}</p>
        )}
        <div className={`mt-2 inline-block h-1 w-12 rounded-full ${tone}`} />
      </CardContent>
    </Card>
  );
}

export function PurchaseView() {
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);
  const [search, setSearch] = React.useState("");
  const [purchaseOpen, setPurchaseOpen] = React.useState(false);
  const [returnOpen, setReturnOpen] = React.useState(false);
  const [detailPurchase, setDetailPurchase] = React.useState<Purchase | null>(null);

  // کوئری با جستجو و فیلتر تاریخ
  const query = React.useMemo(
    () => ({
      page,
      page_size: pageSize,
      ...rangeToQuery(range),
      search: search || undefined,
    }),
    [page, range, search],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["purchases-view", query],
    queryFn: () => api<Paginated<Purchase>>("/workshop/purchases/", { query }),
  });

  const purchases = data?.results ?? [];

  const today = new Date().toISOString().slice(0, 10);
  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().slice(0, 10);

  const monthTotal = React.useMemo(() => {
    return purchases
      .filter((p) => p.purchase_date >= monthStartStr && p.purchase_date <= today)
      .reduce((s, p) => s + parseFloat(p.total_amount ?? "0"), 0);
  }, [purchases, monthStartStr, today]);

  const todayCount = React.useMemo(
    () => purchases.filter((p) => p.purchase_date === today).length,
    [purchases, today],
  );

  const totalQty = React.useMemo(
    () => purchases.reduce((s, p) => s + parseFloat(p.total_qty ?? "0"), 0),
    [purchases],
  );

  return (
    <div className="space-y-4" dir="rtl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5" /> خرید مواد اولیه
          </CardTitle>
          <CardDescription>مدیریت خرید و برگشت از خرید</CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="purchases">
        <TabsList>
          <TabsTrigger value="purchases">خرید مواد اولیه</TabsTrigger>
          <TabsTrigger value="returns">برگشت از خرید</TabsTrigger>
        </TabsList>

        {/* ─── Tab: Purchases ─────────────────────────────────── */}
        <TabsContent value="purchases" className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base">فهرست اسناد خرید</CardTitle>
                <CardDescription>برای مشاهده‌ی جزئیات فاکتور، روی هر سند کلیک کنید</CardDescription>
              </div>
              <Button onClick={() => setPurchaseOpen(true)}>
                <Plus className="h-4 w-4" /> خرید جدید
              </Button>
            </CardHeader>
          </Card>

          {/* Stat cards */}
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard label="خرید این ماه (ریال)" value={formatRial(monthTotal)} loading={isLoading} />
            <StatCard label="خرید امروز" value={`${todayCount} سند`} loading={isLoading} />
            <StatCard label="مقدار کل" value={formatNumber(totalQty)} loading={isLoading} />
            <StatCard label="تعداد کل اسناد" value={purchases.length} loading={isLoading} />
          </div>

          {/* جستجو و فیلتر */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                  <Search className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="جستجو در شماره فاکتور، کارپرداز، توضیحات..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                    className="pr-9"
                  />
                </div>
              </div>
              <DateRangeFilter value={range} onChange={(v) => { setRange(v); setPage(1); }} />
            </CardContent>
          </Card>

          {/* Main table */}
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto scroll-pretty">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">شماره</TableHead>
                      <TableHead className="text-right">تاریخ</TableHead>
                      <TableHead className="text-right">کارپرداز</TableHead>
                      <TableHead className="text-right">انبار</TableHead>
                      <TableHead className="text-right">توضیحات</TableHead>
                      <TableHead className="text-right">مقدار</TableHead>
                      <TableHead className="text-right">مبلغ</TableHead>
                      <TableHead className="text-right">وضعیت</TableHead>
                      <TableHead className="text-right w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {isLoading ? (
                      <TableRow><TableCell colSpan={9} className="p-0"><TableSkeleton rows={8} cols={9} /></TableCell></TableRow>
                    ) : purchases.length === 0 ? (
                      <TableRow><TableCell colSpan={9}><EmptyState description="سند خریدی در این بازه یافت نشد." /></TableCell></TableRow>
                    ) : (
                      purchases.map((p) => (
                        <TableRow
                          key={p.id}
                          className={`cursor-pointer hover:bg-primary/5 ${p.has_returns ? "bg-red-50/50 dark:bg-red-950/20" : ""}`}
                          onClick={() => setDetailPurchase(p)}
                        >
                          <TableCell className="font-mono nums" dir="ltr">
                            {p.purchase_no}
                            {p.has_returns && <Badge variant="destructive" className="mr-1 text-[10px]">برگشت</Badge>}
                          </TableCell>
                          <TableCell className="nums" dir="ltr">{formatDate(p.purchase_date)}</TableCell>
                          <TableCell>{p.contractor_name ?? "—"}</TableCell>
                          <TableCell>{p.warehouse_name ?? "—"}</TableCell>
                          <TableCell className="text-xs text-muted-foreground max-w-[150px] truncate">{p.notes ?? "—"}</TableCell>
                          <TableCell className="nums">{formatNumber(p.total_qty)}</TableCell>
                          <TableCell className="nums">{formatRial(p.total_amount)}</TableCell>
                          <TableCell>
                            <Badge variant={p.status === "posted" ? "default" : "secondary"}>
                              {p.status === "posted" ? "ثبت شد" : p.status === "draft" ? "پیش‌نویس" : "لغو"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <FileText className="h-4 w-4 text-muted-foreground" />
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
              <Pager page={page} pageSize={pageSize} count={data?.count ?? 0} onPage={setPage} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* ─── Tab: Returns ─────────────────────────────────── */}
        <TabsContent value="returns" className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Undo2 className="h-4 w-4" /> برگشت از خرید
                </CardTitle>
                <CardDescription>برگشت کالای خریداری‌شده به تأمین‌کننده</CardDescription>
              </div>
              <Button onClick={() => setReturnOpen(true)}>
                <Plus className="h-4 w-4" /> برگشت جدید
              </Button>
            </CardHeader>
          </Card>

          <ReturnsList />
        </TabsContent>
      </Tabs>

      <PurchaseDialog open={purchaseOpen} onOpenChange={setPurchaseOpen} />
      <PurchaseReturnDialog open={returnOpen} onOpenChange={setReturnOpen} />
      <PurchaseDetailDialog purchase={detailPurchase} onClose={() => setDetailPurchase(null)} />
    </div>
  );
}

// ─── ReturnsList: لیست برگشت‌های خرید ──────────────────────────────
function ReturnsList() {
  const [page, setPage] = React.useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["purchase-returns", page],
    queryFn: () => api<Paginated<PurchaseReturn>>("/workshop/purchase-returns/", { query: { page, page_size: pageSize } }),
  });

  const returns = data?.results ?? [];

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">شماره برگشت</TableHead>
                <TableHead className="text-right">تاریخ</TableHead>
                <TableHead className="text-right">فاکتور خرید</TableHead>
                <TableHead className="text-right">کارپرداز</TableHead>
                <TableHead className="text-right">مقدار برگشتی</TableHead>
                <TableHead className="text-right">مبلغ برگشتی</TableHead>
                <TableHead className="text-right">علت</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={8} className="p-0"><TableSkeleton rows={5} cols={8} /></TableCell></TableRow>
              ) : returns.length === 0 ? (
                <TableRow><TableCell colSpan={8}><EmptyState description="برگشتی ثبت نشده است." /></TableCell></TableRow>
              ) : (
                returns.map((r) => (
                  <TableRow key={r.id} className="bg-red-50/30 dark:bg-red-950/10">
                    <TableCell className="font-mono nums" dir="ltr">{r.return_no}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatDate(r.return_date)}</TableCell>
                    <TableCell className="font-mono nums" dir="ltr">{r.purchase_no ?? "—"}</TableCell>
                    <TableCell>{r.contractor_name ?? "—"}</TableCell>
                    <TableCell className="nums">{formatNumber(r.total_qty)}</TableCell>
                    <TableCell className="nums">{formatRial(r.total_amount)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{r.reason ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant={r.status === "posted" ? "default" : "secondary"}>
                        {r.status === "posted" ? "ثبت شد" : r.status === "draft" ? "پیش‌نویس" : "لغو"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        <Pager page={page} pageSize={pageSize} count={data?.count ?? 0} onPage={setPage} />
      </CardContent>
    </Card>
  );
}

// ─── PurchaseDetailDialog: جزئیات فاکتور خرید (با نشانه‌گذاری برگشتی‌ها) ─────────
function PurchaseDetailDialog({ purchase, onClose }: { purchase: Purchase | null; onClose: () => void }) {
  const { data: detail } = useQuery({
    queryKey: ["purchase-detail", purchase?.id],
    queryFn: () => api<Purchase>(`/workshop/purchases/${purchase!.id}/`),
    enabled: !!purchase,
  });

  // فچ برگشت‌های این فاکتور
  const { data: returnsData } = useQuery({
    queryKey: ["purchase-returns-for-purchase", purchase?.id],
    queryFn: () => api<Paginated<PurchaseReturn>>("/workshop/purchase-returns/", { query: { purchase: purchase!.id } }),
    enabled: !!purchase,
  });

  const data = detail ?? purchase;
  const lines = data?.lines ?? [];
  const returns = returnsData?.results ?? [];

  // محاسبه‌ی مقدار برگشتی هر قلم
  const getReturnedQty = (lineId: number): number => {
    let total = 0;
    returns.forEach((r) => {
      r.lines?.forEach((rl: any) => {
        if (rl.purchase_line === lineId || rl.purchase_line_id === lineId) {
          total += parseFloat(rl.qty || "0");
        }
      });
    });
    return total;
  };

  return (
    <Dialog open={!!purchase} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="sm:max-w-3xl" dir="rtl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" /> فاکتور خرید
          </DialogTitle>
          <DialogDescription>جزئیات سند خرید و اقلام فاکتور</DialogDescription>
        </DialogHeader>

        {data && (
          <div className="space-y-4">
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground">شماره فاکتور:</span>
                  <span className="font-medium font-mono nums mr-2" dir="ltr">{data.purchase_no}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">تاریخ خرید:</span>
                  <span className="font-medium nums mr-2" dir="ltr">{formatDate(data.purchase_date)}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">کارپرداز:</span>
                  <span className="font-medium mr-2">{data.contractor_name ?? "—"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">محل تحویل (انبار):</span>
                  <span className="font-medium mr-2">{data.warehouse_name ?? "—"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">حساب پرداختی:</span>
                  <span className="font-medium mr-2">{data.cash_account_name ?? "—"}</span>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground">سند حسابداری:</span>
                  <span className="font-medium font-mono nums mr-2" dir="ltr">{data.journal_no ?? (data.journal ? `#${data.journal}` : "—")}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-xs text-muted-foreground">وضعیت:</span>
                  <Badge variant={data.status === "posted" ? "default" : "secondary"} className="mr-2">
                    {data.status === "posted" ? "ثبت شد" : data.status === "draft" ? "پیش‌نویس" : "لغو"}
                  </Badge>
                  {returns.length > 0 && (
                    <Badge variant="destructive" className="mr-1">
                      {returns.length} برگشت
                    </Badge>
                  )}
                </div>
                {data.notes && (
                  <div className="col-span-2">
                    <span className="text-xs text-muted-foreground">توضیحات:</span>
                    <span className="font-medium mr-2">{data.notes}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right w-12">ردیف</TableHead>
                    <TableHead className="text-right">شرح کالا</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                    <TableHead className="text-right">تاریخ انقضا</TableHead>
                    <TableHead className="text-right">شماره لات</TableHead>
                    <TableHead className="text-right">فی</TableHead>
                    <TableHead className="text-right">قیمت کل</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground">
                        اقلام فاکتور بارگذاری نشده
                      </TableCell>
                    </TableRow>
                  ) : (
                    lines.map((l, i) => {
                      const lineTotal = l.line_total
                        ? parseFloat(l.line_total)
                        : parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0");
                      const returnedQty = getReturnedQty(l.id);
                      const isReturned = returnedQty > 0;
                      const isFullyReturned = returnedQty >= parseFloat(l.qty || "0");
                      return (
                        <TableRow key={i} className={isReturned ? "text-red-600 bg-red-50/50 dark:bg-red-950/20" : ""}>
                          <TableCell className="font-mono nums">{i + 1}</TableCell>
                          <TableCell className="font-medium">
                            {l.product_name ?? "—"}
                            {isReturned && (
                              <Badge variant="destructive" className="mr-2 text-[10px]">
                                {isFullyReturned ? "کاملاً برگشت شده" : `${returnedQty} برگشت`}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="nums" dir="ltr">
                            {formatNumber(parseFloat(l.qty || "0"))}
                            {isReturned && (
                              <span className="text-red-600 text-xs mr-1">
                                ({returnedQty} برگشت)
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="nums" dir="ltr">{formatDate(l.expiry_date)}</TableCell>
                          <TableCell className="font-mono nums" dir="ltr">{l.lot_no ?? "—"}</TableCell>
                          <TableCell className="nums" dir="ltr">{formatRial(parseFloat(l.unit_price || "0"))}</TableCell>
                          <TableCell className="nums font-semibold" dir="ltr">{formatRial(lineTotal)}</TableCell>
                        </TableRow>
                      );
                    })
                  )}
                  {lines.length > 0 && (
                    <TableRow className="border-t-2 bg-muted/50">
                      <TableCell colSpan={2} className="text-left font-semibold">جمع کل:</TableCell>
                      <TableCell className="nums font-bold" dir="ltr">
                        {formatNumber(lines.reduce((s, l) => s + parseFloat(l.qty || "0"), 0))}
                      </TableCell>
                      <TableCell colSpan={3} className="text-left font-semibold">مبلغ کل:</TableCell>
                      <TableCell className="nums font-bold text-primary" dir="ltr">
                        {formatRial(parseFloat(data.total_amount || "0"))}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex justify-end">
              <Button variant="outline" onClick={onClose}>
                <X className="h-4 w-4 ml-1" /> بستن
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
