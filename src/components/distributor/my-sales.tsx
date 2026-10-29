"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ClipboardList,
  RefreshCw,
  ChevronLeft,
  Plus,
  Calendar,
  Inbox,
  Store as StoreIcon,
  Hash,
} from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { formatRial, formatDate, formatNumber } from "@/lib/format";
import { EmptyState } from "@/components/common";
import { cn } from "@/lib/utils";

interface SaleLine {
  id: number;
  product_id: number;
  product_name: string;
  qty: string;
  unit_price: string;
  line_total: string;
}

interface Sale {
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
  lines: SaleLine[];
}

interface SalesResponse {
  count: number;
  results: Sale[];
}

export function MySales({ onNewSale }: { onNewSale: () => void }) {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["distributor", "my_sales"],
    queryFn: () => api<SalesResponse>("/sales/my_sales/"),
    refetchOnWindowFocus: false,
  });
  const [selected, setSelected] = React.useState<Sale | null>(null);

  if (selected) {
    return <SaleDetail sale={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">فاکتورهای فروش</h2>
          <p className="text-xs text-muted-foreground">
            فروش‌های ثبت‌شده توسط شما.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="text-emerald-700"
        >
          <RefreshCw className={`h-4 w-4 ml-1 ${isFetching ? "animate-spin" : ""}`} />
          به‌روزرسانی
        </Button>
      </div>

      <Button
        onClick={onNewSale}
        className="w-full h-12 bg-emerald-600 hover:bg-emerald-700"
      >
        <Plus className="h-5 w-5 ml-2" />
        ثبت فروش جدید
      </Button>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : (data?.results ?? []).length === 0 ? (
        <EmptyState
          title="فاکتوری ثبت نشده"
          description="هنوز فروشی توسط شما ثبت نشده است."
        />
      ) : (
        <div className="space-y-2">
          {data?.results.map((s) => {
            const isPosted = s.status === "posted";
            return (
              <Card
                key={s.id}
                onClick={() => setSelected(s)}
                className="border-border/60 hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer"
              >
                <CardContent className="p-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0 flex-1">
                      <div
                        className={cn(
                          "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white",
                          s.sales_type === "consignment"
                            ? "bg-gradient-to-br from-amber-500 to-orange-500"
                            : "bg-gradient-to-br from-emerald-500 to-teal-500"
                        )}
                      >
                        <ClipboardList className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-bold nums" dir="ltr">
                            {s.sale_no}
                          </p>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-[10px] h-5",
                              isPosted
                                ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                                : "border-amber-300 bg-amber-50 text-amber-700"
                            )}
                          >
                            {s.status_display}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
                          <StoreIcon className="h-3.5 w-3.5" />
                          <span className="truncate">{s.store_name}</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(s.sale_date)}
                          </span>
                          <span>·</span>
                          <span className="font-medium">{s.sales_type_display}</span>
                          <span>·</span>
                          <span>{s.payment_method_display}</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-left shrink-0">
                      <p className="text-sm font-bold text-emerald-700 nums">
                        {formatRial(s.total_amount)}
                      </p>
                      <div className="flex items-center gap-1 text-[11px] text-muted-foreground mt-1">
                        <Hash className="h-3 w-3" />
                        {formatNumber(s.lines?.length ?? 0)} قلم
                      </div>
                    </div>
                  </div>
                  {s.notes && (
                    <p className="mt-2 text-[11px] text-muted-foreground border-t pt-2 italic">
                      «{s.notes}»
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SaleDetail({ sale, onBack }: { sale: Sale; onBack: () => void }) {
  const totalAmount = parseFloat(sale.total_amount ?? "0");
  const paidAmount = parseFloat(sale.paid_amount ?? "0");
  const remaining = totalAmount - paidAmount;

  return (
    <div className="space-y-3">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-emerald-700"
      >
        <ChevronLeft className="h-4 w-4" />
        بازگشت به فاکتورها
      </button>

      {/* Invoice header */}
      <Card className="border-emerald-200 bg-gradient-to-l from-emerald-50 to-teal-50/40">
        <CardContent className="p-4 space-y-2">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-muted-foreground">شماره فاکتور</p>
              <p className="text-lg font-bold nums" dir="ltr">{sale.sale_no}</p>
            </div>
            <Badge
              variant="outline"
              className={
                sale.status === "posted"
                  ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                  : "border-amber-300 bg-amber-50 text-amber-700"
              }
            >
              {sale.status_display}
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <DetailRow label="فروشگاه" value={sale.store_name} />
            <DetailRow label="تاریخ" value={formatDate(sale.sale_date)} />
            <DetailRow label="نوع فروش" value={sale.sales_type_display} />
            <DetailRow label="نحوه پرداخت" value={sale.payment_method_display} />
          </div>
        </CardContent>
      </Card>

      {/* Line items */}
      <div>
        <p className="text-xs font-semibold text-muted-foreground mb-1.5">اقلام فاکتور:</p>
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            {sale.lines.map((l, i) => {
              const qty = parseFloat(l.qty ?? "0");
              const price = parseFloat(l.unit_price ?? "0");
              const total = parseFloat(l.line_total ?? "0") || qty * price;
              return (
                <div
                  key={l.id}
                  className={cn(
                    "flex items-center justify-between gap-2 p-3",
                    i < sale.lines.length - 1 && "border-b"
                  )}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700 text-xs font-bold nums">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{l.product_name}</p>
                      <p className="text-[11px] text-muted-foreground nums" dir="ltr">
                        {formatNumber(qty)} × {formatRial(price)}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm font-bold text-emerald-700 nums shrink-0">
                    {formatRial(total)}
                  </p>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>

      {/* Totals */}
      <Card className="border-emerald-200">
        <CardContent className="p-3 space-y-1.5 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">جمع کل</span>
            <span className="font-bold nums">{formatRial(totalAmount)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">پرداخت‌شده</span>
            <span className="font-bold text-emerald-700 nums">
              {formatRial(paidAmount)}
            </span>
          </div>
          <div className="flex items-center justify-between border-t pt-1.5 mt-1.5">
            <span className="text-muted-foreground">مانده</span>
            <span
              className={cn(
                "font-bold nums",
                remaining > 0 ? "text-amber-700" : "text-emerald-700"
              )}
            >
              {formatRial(remaining)}
            </span>
          </div>
        </CardContent>
      </Card>

      {sale.notes && (
        <Card>
          <CardContent className="p-3">
            <p className="text-xs font-semibold text-muted-foreground mb-1">یادداشت:</p>
            <p className="text-sm">{sale.notes}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/60 px-2 py-1.5">
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="text-xs font-medium">{value}</p>
    </div>
  );
}
