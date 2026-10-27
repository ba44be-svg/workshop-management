"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Send } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { MOCK_WORKSHOP_ISSUES } from "@/lib/mock-data";
import { formatNumber, formatRial, formatDate } from "@/lib/format";
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
import { WorkshopIssueDialog } from "@/components/dialogs/workshop-issue-dialog";
import { DateRangeFilter, DEFAULT_RANGE, rangeToQuery, type DateRangeValue } from "@/components/date-range-filter";

type Issue = (typeof MOCK_WORKSHOP_ISSUES)[number] & {
  employee_name?: string;
  from_warehouse_name?: string;
  to_warehouse_name?: string;
};

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

export function WorkshopIssueView() {
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [range, setRange] = React.useState<DateRangeValue>(DEFAULT_RANGE);
  const [issueOpen, setIssueOpen] = React.useState(false);

  const query = React.useMemo(
    () => ({ page, page_size: pageSize, ...rangeToQuery(range) }),
    [page, range],
  );

  const { data, isLoading } = useQuery({
    queryKey: ["workshop-issues-view", query],
    queryFn: () => api<Paginated<Issue>>("/workshop/issues/", { query }),
  });

  const issues = data?.results ?? [];

  const today = new Date().toISOString().slice(0, 10);
  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().slice(0, 10);

  const monthQty = React.useMemo(() => {
    return issues
      .filter((i) => i.issue_date >= monthStartStr && i.issue_date <= today)
      .reduce((s, i) => s + parseFloat(i.total_qty ?? "0"), 0);
  }, [issues, monthStartStr, today]);

  const todayCount = issues.filter((i) => i.issue_date === today).length;
  const totalQty = issues.reduce((s, i) => s + parseFloat(i.total_qty ?? "0"), 0);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Send className="h-5 w-5" /> حواله به کارگاه
            </CardTitle>
            <CardDescription>فهرست حواله‌های مواد اولیه به کارگاه‌ها</CardDescription>
          </div>
          <Button onClick={() => setIssueOpen(true)}>
            <Plus className="h-4 w-4" /> حواله جدید
          </Button>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="مقدار حواله این ماه" value={formatNumber(monthQty)} loading={isLoading} />
        <StatCard label="حواله امروز" value={`${todayCount} سند`} loading={isLoading} />
        <StatCard label="مقدار کل" value={formatNumber(totalQty)} loading={isLoading} />
        <StatCard label="تعداد کل اسناد" value={issues.length} loading={isLoading} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">فهرست حواله‌ها</CardTitle>
          <CardDescription>حواله‌های اخیر به کارگاه‌ها</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">شماره</TableHead>
                  <TableHead className="text-right">تاریخ</TableHead>
                  <TableHead className="text-right">شخص تحویل‌گیرنده</TableHead>
                  <TableHead className="text-right">انبار مبدأ</TableHead>
                  <TableHead className="text-right">کارگاه مقصد</TableHead>
                  <TableHead className="text-right">مقدار</TableHead>
                  <TableHead className="text-right">وضعیت</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="p-0">
                      <TableSkeleton rows={8} cols={7} />
                    </TableCell>
                  </TableRow>
                ) : issues.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <EmptyState description="حواله‌ای در این بازه یافت نشد." />
                    </TableCell>
                  </TableRow>
                ) : (
                  issues.map((i) => (
                    <TableRow key={i.id}>
                      <TableCell className="font-mono nums" dir="ltr">{i.issue_no}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(i.issue_date)}</TableCell>
                      <TableCell>{i.employee_name || i.contractor_name || "—"}</TableCell>
                      <TableCell>{i.from_warehouse_name ?? i.from_warehouse ?? "—"}</TableCell>
                      <TableCell>{i.to_warehouse_name ?? i.to_warehouse ?? "—"}</TableCell>
                      <TableCell className="nums">{formatNumber(i.total_qty)}</TableCell>
                      <TableCell>
                        <Badge variant={i.status === "posted" ? "default" : "secondary"}>
                          {i.status === "posted" ? "ثبت شد" : i.status === "draft" ? "پیش‌نویس" : "لغو"}
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
          <CardTitle className="text-base">گزارش حواله در بازه</CardTitle>
          <CardDescription>مجموع حواله‌ها را در یک بازه‌ی زمانی مشاهده کنید</CardDescription>
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
              <p className="font-medium nums">{issues.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <WorkshopIssueDialog open={issueOpen} onOpenChange={setIssueOpen} />
    </div>
  );
}
