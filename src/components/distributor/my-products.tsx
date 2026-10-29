"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Package, RefreshCw, Inbox, Calendar, Hash, Truck } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRial, formatNumber, formatDate } from "@/lib/format";
import { EmptyState } from "@/components/common";

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
  distributor_id: number;
  distributor_name: string;
  status: string;
  total_amount: string;
  lines: DispatchLine[];
}

interface DispatchesResponse {
  count: number;
  results: DispatchItem[];
  distributor_id: number;
  distributor_name: string;
}

export function MyProducts() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["distributor", "my_dispatches"],
    queryFn: () => api<DispatchesResponse>("/dispatch/my_dispatches/"),
    refetchOnWindowFocus: false,
  });

  // Flatten to a list of products in hand.
  const products = React.useMemo(() => {
    const out: Array<{
      dispatch_no: string;
      dispatch_date: string;
      line: DispatchLine;
    }> = [];
    for (const d of data?.results ?? []) {
      for (const l of d.lines ?? []) {
        out.push({ dispatch_no: d.dispatch_no, dispatch_date: d.dispatch_date, line: l });
      }
    }
    return out;
  }, [data]);

  const totalValue = products.reduce(
    (s, p) => s + parseFloat(p.line.line_total ?? "0"),
    0
  );
  const totalQty = products.reduce(
    (s, p) => s + parseFloat(p.line.qty ?? "0"),
    0
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">کالاهای در دست</h2>
          <p className="text-xs text-muted-foreground">
            کالاهای تحویل‌شده به شما که هنوز نفروخته‌اید.
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

      {/* Summary card */}
      <Card className="border-emerald-200 bg-gradient-to-l from-emerald-50 to-teal-50/50">
        <CardContent className="grid grid-cols-2 gap-3 p-4">
          <div>
            <p className="text-xs text-muted-foreground">تعداد قلم</p>
            {isLoading ? (
              <Skeleton className="mt-1 h-6 w-20" />
            ) : (
              <p className="text-lg font-bold nums">
                {formatNumber(products.length)}
              </p>
            )}
          </div>
          <div>
            <p className="text-xs text-muted-foreground">جمع مقدار</p>
            {isLoading ? (
              <Skeleton className="mt-1 h-6 w-20" />
            ) : (
              <p className="text-lg font-bold nums">{formatNumber(totalQty)}</p>
            )}
          </div>
          <div className="col-span-2 border-t pt-2 mt-1">
            <p className="text-xs text-muted-foreground">ارزش کل کالا</p>
            {isLoading ? (
              <Skeleton className="mt-1 h-6 w-32" />
            ) : (
              <p className="text-base font-bold text-emerald-700 nums">
                {formatRial(totalValue)}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* List */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <EmptyState
          title="کالایی در دست نیست"
          description="هنوز کالایی به شما تحویل داده نشده است."
        />
      ) : (
        <div className="space-y-2">
          {products.map((p, i) => {
            const qty = parseFloat(p.line.qty ?? "0");
            const price = parseFloat(p.line.unit_price ?? "0");
            const total = parseFloat(p.line.line_total ?? "0") || qty * price;
            return (
              <Card key={`${p.dispatch_no}-${p.line.id}-${i}`} className="overflow-hidden border-border/60">
                <CardContent className="p-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                        <Package className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold leading-tight">
                          {p.line.product_name}
                        </p>
                        <p className="text-[11px] text-muted-foreground nums mt-0.5" dir="ltr">
                          {p.line.product_code}
                        </p>
                        <div className="flex flex-wrap gap-2 mt-1.5 text-[11px] text-muted-foreground">
                          <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 text-amber-700 px-1.5 py-0.5">
                            <Truck className="h-3 w-3" />
                            {p.dispatch_no}
                          </span>
                          <span className="inline-flex items-center gap-1 rounded-md bg-muted px-1.5 py-0.5">
                            <Calendar className="h-3 w-3" />
                            {formatDate(p.dispatch_date)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 rounded-lg bg-muted/30 p-2.5 text-center">
                    <div>
                      <p className="text-[10px] text-muted-foreground">مقدار</p>
                      <p className="text-sm font-bold nums">{formatNumber(qty)}</p>
                    </div>
                    <div className="border-x">
                      <p className="text-[10px] text-muted-foreground">فی</p>
                      <p className="text-xs font-semibold nums" dir="ltr">
                        {formatRial(price)}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground">ارزش کل</p>
                      <p className="text-xs font-bold text-emerald-700 nums">
                        {formatRial(total)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
