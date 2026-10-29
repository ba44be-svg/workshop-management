"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Warehouse, Boxes, AlertTriangle, ArrowRightLeft } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { MOCK_LOTS, MOCK_STOCK_BALANCE, MOCK_PRODUCTS } from "@/lib/mock-data";
import { formatDate, formatNumber } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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

type Lot = (typeof MOCK_LOTS)[number] & {
  product_name?: string;
  product_code?: string;
  warehouse_name?: string;
  days_to_expiry?: number;
};
type Balance = (typeof MOCK_STOCK_BALANCE)[number] & {
  product_name?: string;
  product_code?: string;
  warehouse_name?: string;
  warehouse?: number;
  total_qty?: string;
  total_value?: string;
};
type Product = (typeof MOCK_PRODUCTS)[number] & {
  is_finished_good?: boolean;
};

export function InventoryView() {
  return (
    <div className="space-y-4" dir="rtl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Warehouse className="h-5 w-5" /> انبار
          </CardTitle>
          <CardDescription>مدیریت موجودی مواد اولیه و محصولات</CardDescription>
        </CardHeader>
      </Card>

      <Tabs defaultValue="raw_materials">
        <TabsList>
          <TabsTrigger value="raw_materials">
            <Boxes className="h-4 w-4 ml-1" /> مواد اولیه (کالاهای خریداری)
          </TabsTrigger>
          <TabsTrigger value="finished_goods">
            <Boxes className="h-4 w-4 ml-1" /> محصولات تولیدی
          </TabsTrigger>
          <TabsTrigger value="movements">
            <ArrowRightLeft className="h-4 w-4 ml-1" /> ورود و خروج
          </TabsTrigger>
        </TabsList>

        {/* ─── تب مواد اولیه ─────────────────────────────────── */}
        <TabsContent value="raw_materials" className="space-y-4">
          <RawMaterialsTab />
        </TabsContent>

        {/* ─── تب محصولات ─────────────────────────────────── */}
        <TabsContent value="finished_goods" className="space-y-4">
          <FinishedGoodsTab />
        </TabsContent>

        {/* ─── تب حرکت‌ها ─────────────────────────────────── */}
        <TabsContent value="movements" className="space-y-4">
          <MovementsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ─── تب مواد اولیه ──────────────────────────────────────────────────────
function RawMaterialsTab() {
  const { data: whData } = useQuery({
    queryKey: ["warehouses-raw"],
    queryFn: () => api<Paginated<any>>("/inventory/warehouses/", { query: { page: 1, page_size: 200, type: "raw_materials" } }),
  });
  const rawWhIds = React.useMemo(() => (whData?.results ?? []).map((w: any) => w.id), [whData]);

  const { data, isLoading } = useQuery({
    queryKey: ["balances-raw", rawWhIds],
    queryFn: () => api<Paginated<Balance>>("/inventory/balances/", { query: { page: 1, page_size: 200 } }),
  });

  const balances = React.useMemo(() => {
    const all = data?.results ?? [];
    if (rawWhIds.length === 0) return all;
    return all.filter((b) => rawWhIds.includes(b.warehouse));
  }, [data, rawWhIds]);

  const totalQty = balances.reduce((s, b) => s + parseFloat(b.total_qty ?? "0"), 0);
  const totalValue = balances.reduce((s, b) => s + parseFloat(b.total_value ?? "0"), 0);

  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="تعداد اقلام" value={balances.length} loading={isLoading} />
        <StatCard label="مقدار کل" value={formatNumber(totalQty)} loading={isLoading} />
        <StatCard label="ارزش کل (ریال)" value={formatNumber(totalValue)} loading={isLoading} />
        <StatCard label="انبارها" value={rawWhIds.length} loading={isLoading} />
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">انبار</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">ارزش</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={5} className="p-0"><TableSkeleton rows={8} cols={5} /></TableCell></TableRow>
                ) : balances.length === 0 ? (
                  <TableRow><TableCell colSpan={5}><EmptyState description="موجودی مواد اولیه یافت نشد." /></TableCell></TableRow>
                ) : (
                  balances.map((b, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{b.product_name ?? "—"}</TableCell>
                      <TableCell className="font-mono nums" dir="ltr">{b.product_code ?? "—"}</TableCell>
                      <TableCell>{b.warehouse_name ?? "—"}</TableCell>
                      <TableCell className="nums font-semibold" dir="ltr">{formatNumber(parseFloat(b.total_qty ?? "0"))}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(parseFloat(b.total_value ?? "0"))}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

// ─── تب محصولات تولیدی ──────────────────────────────────────────────────
function FinishedGoodsTab() {
  const { data: whData } = useQuery({
    queryKey: ["warehouses-finished"],
    queryFn: () => api<Paginated<any>>("/inventory/warehouses/", { query: { page: 1, page_size: 200, type: "finished_goods" } }),
  });
  const finishedWhIds = React.useMemo(() => (whData?.results ?? []).map((w: any) => w.id), [whData]);

  const { data, isLoading } = useQuery({
    queryKey: ["balances-finished", finishedWhIds],
    queryFn: () => api<Paginated<Balance>>("/inventory/balances/", { query: { page: 1, page_size: 200 } }),
  });

  const balances = React.useMemo(() => {
    const all = data?.results ?? [];
    if (finishedWhIds.length === 0) return all;
    return all.filter((b) => finishedWhIds.includes(b.warehouse));
  }, [data, finishedWhIds]);

  const totalQty = balances.reduce((s, b) => s + parseFloat(b.total_qty ?? "0"), 0);
  const totalValue = balances.reduce((s, b) => s + parseFloat(b.total_value ?? "0"), 0);

  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols=4">
        <StatCard label="تعداد اقلام" value={balances.length} loading={isLoading} />
        <StatCard label="مقدار کل" value={formatNumber(totalQty)} loading={isLoading} />
        <StatCard label="ارزش کل (ریال)" value={formatNumber(totalValue)} loading={isLoading} />
        <StatCard label="انبارها" value={finishedWhIds.length} loading={isLoading} />
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">انبار</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">ارزش</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={5} className="p-0"><TableSkeleton rows={8} cols={5} /></TableCell></TableRow>
                ) : balances.length === 0 ? (
                  <TableRow><TableCell colSpan={5}><EmptyState description="موجودی محصولات یافت نشد." /></TableCell></TableRow>
                ) : (
                  balances.map((b, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{b.product_name ?? "—"}</TableCell>
                      <TableCell className="font-mono nums" dir="ltr">{b.product_code ?? "—"}</TableCell>
                      <TableCell>{b.warehouse_name ?? "—"}</TableCell>
                      <TableCell className="nums font-semibold" dir="ltr">{formatNumber(parseFloat(b.total_qty ?? "0"))}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(parseFloat(b.total_value ?? "0"))}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

// ─── تب حرکت‌ها ──────────────────────────────────────────────────────────
function MovementsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["movements-all"],
    queryFn: () => api<Paginated<any>>("/inventory/movements/", { query: { page: 1, page_size: 50 } }).catch(() => null),
  });

  const movements = data?.results ?? [];

  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">تاریخ</TableHead>
                <TableHead className="text-right">نوع</TableHead>
                <TableHead className="text-right">محصول</TableHead>
                <TableHead className="text-right">انبار</TableHead>
                <TableHead className="text-right">مقدار</TableHead>
                <TableHead className="text-right">مرجع</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={8} cols={6} /></TableCell></TableRow>
              ) : movements.length === 0 ? (
                <TableRow><TableCell colSpan={6}><EmptyState description="حرکتی ثبت نشده است." /></TableCell></TableRow>
              ) : (
                movements.map((m, i) => (
                  <TableRow key={i}>
                    <TableCell className="nums" dir="ltr">{formatDate(m.created_at)}</TableCell>
                    <TableCell>
                      <Badge variant={m.movement_type === "in" ? "default" : m.movement_type === "out" ? "destructive" : "secondary"}>
                        {m.movement_type === "in" ? "ورود" : m.movement_type === "out" ? "خروج" : m.movement_type === "transfer" ? "انتقال" : "تولید"}
                      </Badge>
                    </TableCell>
                    <TableCell>{m.product_name ?? m.product ?? "—"}</TableCell>
                    <TableCell>{m.warehouse_name ?? m.warehouse ?? "—"}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(parseFloat(m.qty ?? "0"))}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{m.ref_doc_type ?? "—"}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── StatCard ────────────────────────────────────────────────────────────
function StatCard({ label, value, loading, tone = "bg-primary/10 text-primary" }: { label: string; value: string | number; loading?: boolean; tone?: string }) {
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
