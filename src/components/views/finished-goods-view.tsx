"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Boxes, Plus, PackageCheck } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { formatNumber, formatDate } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TableSkeleton, EmptyState } from "@/components/common";
import { DateRangeFilter, DEFAULT_RANGE, rangeToQuery, type DateRangeValue } from "@/components/date-range-filter";
import { ProductOutputDialog } from "@/components/dialogs/product-output-dialog";

interface StockRow {
  id: number;
  product_id: number;
  product_code?: string;
  product_name?: string;
  warehouse: number;
  warehouse_code?: string;
  warehouse_name?: string;
  total_qty: string;
  total_value?: string;
  last_lot?: number | null;
  updated_at?: string;
}

interface MovementRow {
  id: number;
  product: number;
  product_code?: string;
  product_name?: string;
  warehouse: number;
  movement_type: string;
  qty: string;
  ref_doc_type?: string;
  ref_doc_id?: number | null;
  created_at: string;
}

function StatCard({ label, value, loading }: { label: string; value: string | number; loading?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-[11px] text-muted-foreground">{label}</p>
        {loading ? (
          <Skeleton className="mt-2 h-6 w-20" />
        ) : (
          <p className="mt-1 text-lg font-bold nums">{value}</p>
        )}
      </CardContent>
    </Card>
  );
}

const WAREHOUSE_TYPE_LABEL: Record<string, string> = {
  main: "اصلی",
  raw_materials: "مواد اولیه",
  finished_goods: "محصولات",
  workshop: "کارگاه",
  store: "فروشگاه",
  virtual: "مجازی",
};

export function FinishedGoodsView() {
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);
  const [outputOpen, setOutputOpen] = React.useState(false);

  // 1) Stock balances filtered to finished_goods warehouses
  const finishedWhQuery = React.useMemo(() => ({ page: 1, page_size: 200, type: "finished_goods" }), []);
  const { data: finishedWhData } = useQuery({
    queryKey: ["warehouses-finished-goods"],
    queryFn: () => api<Paginated<any>>("/inventory/warehouses/", { query: finishedWhQuery }),
  });
  const finishedWarehouses = finishedWhData?.results ?? [];
  const finishedWhIds = React.useMemo(
    () => finishedWarehouses.map((w: any) => w.id),
    [finishedWarehouses],
  );

  // 2) StockBalance query — fetch balances for all finished_goods warehouses
  // Use multiple warehouse filter via repeated query params — backend supports only single
  // warehouse filter, so we fetch all balances and filter client-side.
  const { data: balancesData, isLoading: balancesLoading } = useQuery({
    queryKey: ["stock-balances-finished"],
    queryFn: () => api<Paginated<StockRow>>("/inventory/balances/", { query: { page: 1, page_size: 200 } }),
  });
  const balances = React.useMemo(() => {
    const all = balancesData?.results ?? [];
    if (finishedWhIds.length === 0) return all;
    return all.filter((b) => finishedWhIds.includes(b.warehouse));
  }, [balancesData, finishedWhIds]);

  // 3) Movements for the finished_goods warehouses in the date range
  const movQuery = React.useMemo(
    () => ({ page: 1, page_size: 100, ...rangeToQuery(range) }),
    [range],
  );
  const { data: movementsData, isLoading: movementsLoading } = useQuery({
    queryKey: ["movements-finished", movQuery],
    queryFn: () =>
      api<Paginated<MovementRow>>("/inventory/movements/", { query: movQuery }).catch(() => null),
  });
  const movements = (movementsData?.results ?? []) as MovementRow[];
  const filteredMovements = React.useMemo(() => {
    if (finishedWhIds.length === 0) return movements;
    return movements.filter((m) => finishedWhIds.includes(m.warehouse));
  }, [movements, finishedWhIds]);

  const totalQty = React.useMemo(
    () => balances.reduce((s, b) => s + parseFloat(b.total_qty ?? "0"), 0),
    [balances],
  );
  const productsCount = React.useMemo(
    () => new Set(balances.map((b) => b.product_id)).size,
    [balances],
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Boxes className="h-5 w-5" /> انبار محصول
            </CardTitle>
            <CardDescription>موجودی محصولات تمام‌شده و حرکت‌های انبار محصول</CardDescription>
          </div>
          <Button onClick={() => setOutputOpen(true)}>
            <PackageCheck className="h-4 w-4" /> خروج محصول
          </Button>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="موجودی کل" value={formatNumber(totalQty)} loading={balancesLoading} />
        <StatCard label="انبار محصول" value={finishedWarehouses.length} loading={false} />
        <StatCard label="محصولات" value={productsCount} loading={balancesLoading} />
        <StatCard label="حرکت‌ها در بازه" value={filteredMovements.length} loading={movementsLoading} />
      </div>

      {/* StockBalance table for finished_goods warehouses */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">موجودی محصولات تمام‌شده</CardTitle>
          <CardDescription>موجودی هر محصول در انبارهای نوع «محصول»</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">کد محصول</TableHead>
                  <TableHead className="text-right">نام محصول</TableHead>
                  <TableHead className="text-right">انبار</TableHead>
                  <TableHead className="text-right">موجودی</TableHead>
                  <TableHead className="text-right">آخرین به‌روزرسانی</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {balancesLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <TableSkeleton rows={6} cols={5} />
                    </TableCell>
                  </TableRow>
                ) : balances.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <EmptyState description="موجودی محصولی در انبار محصول ثبت نشده." />
                    </TableCell>
                  </TableRow>
                ) : (
                  balances.map((b, idx) => (
                    <TableRow key={`${b.id}-${idx}`}>
                      <TableCell className="font-mono nums" dir="ltr">{b.product_code ?? `#${b.product_id}`}</TableCell>
                      <TableCell className="font-medium">{b.product_name ?? "—"}</TableCell>
                      <TableCell>{b.warehouse_name ?? b.warehouse_code ?? "—"}</TableCell>
                      <TableCell className="nums">{formatNumber(b.total_qty)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(b.updated_at ?? null)}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Movements report */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">حرکت‌های انبار محصول</CardTitle>
          <CardDescription>ورود و خروج محصولات در بازه‌ی انتخاب‌شده</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <DateRangeFilter value={range} onChange={setRange} />
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">تاریخ</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">نوع حرکت</TableHead>
                  <TableHead className="text-right">مقدار</TableHead>
                  <TableHead className="text-right">سند مرجع</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {movementsLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <TableSkeleton rows={5} cols={5} />
                    </TableCell>
                  </TableRow>
                ) : filteredMovements.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <EmptyState description="حرکتی در این بازه ثبت نشده." />
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredMovements.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="nums" dir="ltr">{formatDate(m.created_at)}</TableCell>
                      <TableCell>{m.product_name ?? m.product_code ?? `#${m.product}`}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            m.movement_type === "in" || m.movement_type === "production"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {m.movement_type === "in" ? "ورود"
                            : m.movement_type === "out" ? "خروج"
                            : m.movement_type === "transfer" ? "انتقال"
                            : m.movement_type === "return" ? "برگشت"
                            : m.movement_type === "adjustment" ? "تعدیل"
                            : m.movement_type === "production" ? "تولید"
                            : m.movement_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="nums">{formatNumber(m.qty)}</TableCell>
                      <TableCell className="font-mono nums text-xs" dir="ltr">
                        {m.ref_doc_type ?? "—"}{m.ref_doc_id ? `#${m.ref_doc_id}` : ""}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <ProductOutputDialog open={outputOpen} onOpenChange={setOutputOpen} />
    </div>
  );
}
