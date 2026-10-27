"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, PackageCheck } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { MOCK_PRODUCTION_OUTPUTS, MOCK_BATCHES } from "@/lib/mock-data";
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
import { Pager, TableSkeleton, EmptyState } from "@/components/common";
import { ProductOutputDialog } from "@/components/dialogs/product-output-dialog";
import { DateRangeFilter, DEFAULT_RANGE, rangeToQuery, type DateRangeValue } from "@/components/date-range-filter";

type Output = (typeof MOCK_PRODUCTION_OUTPUTS)[number];
type Batch = (typeof MOCK_BATCHES)[number];

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

export function ProductOutputView() {
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);
  const [outputOpen, setOutputOpen] = React.useState(false);

  const query = React.useMemo(
    () => ({ page, page_size: pageSize, ...rangeToQuery(range) }),
    [page, range],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["product-outputs-view", query],
    queryFn: () =>
      api<Paginated<Output>>("/production/outputs/", { query }).catch(() => null),
  });
  const outputs = ((data as Paginated<Output> | null)?.results ?? MOCK_PRODUCTION_OUTPUTS) as Output[];

  const today = new Date().toISOString().slice(0, 10);
  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().slice(0, 10);

  const monthQty = React.useMemo(() => {
    return outputs
      .filter((o) => (o.output_date ?? "").slice(0, 10) >= monthStartStr && (o.output_date ?? "").slice(0, 10) <= today)
      .reduce((s, o) => s + parseFloat(o.total_qty ?? "0"), 0);
  }, [outputs, monthStartStr, today]);

  const todayCount = outputs.filter((o) => (o.output_date ?? "").slice(0, 10) === today).length;
  const totalQty = outputs.reduce((s, o) => s + parseFloat(o.total_qty ?? "0"), 0);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <PackageCheck className="h-5 w-5" /> خروج از کارگاه
            </CardTitle>
            <CardDescription>فهرست خروج‌های محصول از کارگاه به انبار محصول</CardDescription>
          </div>
          <Button onClick={() => setOutputOpen(true)}>
            <Plus className="h-4 w-4" /> خروج جدید
          </Button>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="خروج این ماه" value={formatNumber(monthQty)} loading={isLoading} />
        <StatCard label="خروج امروز" value={`${todayCount} سند`} loading={isLoading} />
        <StatCard label="مقدار کل" value={formatNumber(totalQty)} loading={isLoading} />
        <StatCard label="تعداد کل" value={outputs.length} loading={isLoading} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">فهرست خروج‌ها</CardTitle>
          <CardDescription>خروج‌های اخیر از کارگاه</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">شماره</TableHead>
                  <TableHead className="text-right">تاریخ</TableHead>
                  <TableHead className="text-right">محصول</TableHead>
                  <TableHead className="text-right">بچ</TableHead>
                  <TableHead className="text-right">مقدار</TableHead>
                  <TableHead className="text-right">وضعیت</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="p-0">
                      <TableSkeleton rows={8} cols={6} />
                    </TableCell>
                  </TableRow>
                ) : outputs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <EmptyState description="خروجی در این بازه یافت نشد." />
                    </TableCell>
                  </TableRow>
                ) : (
                  outputs.map((o) => (
                    <TableRow key={o.id}>
                      <TableCell className="font-mono nums" dir="ltr">{o.output_no}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(o.output_date)}</TableCell>
                      <TableCell>{o.product_name ?? "—"}</TableCell>
                      <TableCell className="font-mono nums" dir="ltr">{o.batch_no ?? "—"}</TableCell>
                      <TableCell className="nums">{formatNumber(o.total_qty)}</TableCell>
                      <TableCell>
                        <Badge variant={o.status === "posted" ? "default" : "secondary"}>
                          {o.status === "posted" ? "ثبت شد" : "پیش‌نویس"}
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

      <Card>
        <CardHeader>
          <CardTitle className="text-base">گزارش خروج در بازه</CardTitle>
          <CardDescription>مجموع خروج‌ها را در یک بازه‌ی زمانی مشاهده کنید</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <DateRangeFilter value={range} onChange={(v) => { setRange(v); setPage(1); }} />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">بازه</p>
              <p className="font-medium nums" dir="ltr">
                {range.from ? formatDate(range.from) : "—"} ← {range.to ? formatDate(range.to) : "—"}
              </p>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">مجموع مقدار</p>
              <p className="font-medium nums">{formatNumber(totalQty)}</p>
            </div>
            <div className="rounded-md border p-3">
              <p className="text-xs text-muted-foreground">تعداد اسناد</p>
              <p className="font-medium nums">{outputs.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <ProductOutputDialog open={outputOpen} onOpenChange={setOutputOpen} />
    </div>
  );
}
