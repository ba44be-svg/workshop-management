"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, type Paginated, ApiError } from "@/lib/api";
import { MOCK_PURCHASES, MOCK_PURCHASE_RETURNS } from "@/lib/mock-data";
import { formatNumber, formatRial, formatDate } from "@/lib/format";
import { todayISO } from "@/lib/calendar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DatePicker } from "@/components/dialogs/datepicker";

type Purchase = (typeof MOCK_PURCHASES)[number] & {
  lines?: Array<{
    id: number;
    product: number;
    product_name: string;
    qty: string;
    unit_price: string;
    lot_no: string;
    expiry_date: string;
  }>;
};

type PurchaseReturn = (typeof MOCK_PURCHASE_RETURNS)[number] & {
  lines?: Array<{
    purchase_line: number;
    purchase_line_id?: number;
    qty: string;
  }>;
};

interface PurchaseReturnDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

export function PurchaseReturnDialog({ open, onOpenChange }: PurchaseReturnDialogProps) {
  const qc = useQueryClient();
  const [returnDate, setReturnDate] = React.useState<string | null>(todayISO());
  const [purchaseId, setPurchaseId] = React.useState<string>("");
  const [reason, setReason] = React.useState("");
  const [returnLines, setReturnLines] = React.useState<Array<{
    purchase_line_id: number;
    product_name: string;
    qty: string;
    max_qty: number;
    returned_qty: number; // مقدار قبلاً برگشت‌شده
    unit_price: string;
    selected: boolean;
  }>>([]);

  // فچ لیست فاکتورها
  const { data: purchasesData } = useQuery({
    queryKey: ["purchases-for-return"],
    queryFn: () => api<Paginated<Purchase>>("/workshop/purchases/", { query: { page: 1, page_size: 50 } }),
  });
  const purchases = purchasesData?.results ?? MOCK_PURCHASES;

  // فچ جزئیات فاکتور
  const { data: purchaseDetail } = useQuery({
    queryKey: ["purchase-detail", purchaseId],
    queryFn: () => api<Purchase>(`/workshop/purchases/${purchaseId}/`),
    enabled: !!purchaseId,
  });

  // فچ برگشت‌های قبلی این فاکتور
  const { data: returnsData } = useQuery({
    queryKey: ["purchase-returns-for", purchaseId],
    queryFn: () => api<Paginated<PurchaseReturn>>("/workshop/purchase-returns/", { query: { purchase: purchaseId } }),
    enabled: !!purchaseId,
  });

  // وقتی جزئیات فاکتور و برگشت‌ها لود شد، اقلام رو آماده کن
  React.useEffect(() => {
    if (purchaseDetail?.lines) {
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

      setReturnLines(
        purchaseDetail.lines.map((l) => {
          const returnedQty = getReturnedQty(l.id);
          const maxQty = parseFloat(l.qty) - returnedQty;
          return {
            purchase_line_id: l.id,
            product_name: l.product_name,
            qty: "0",
            max_qty: maxQty,
            returned_qty: returnedQty,
            unit_price: l.unit_price,
            selected: false,
          };
        })
      );
    }
  }, [purchaseDetail, returnsData]);

  const totalQty = returnLines
    .filter((l) => l.selected)
    .reduce((s, l) => s + parseFloat(l.qty || "0"), 0);
  const totalAmount = returnLines
    .filter((l) => l.selected)
    .reduce((s, l) => s + parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0"), 0);

  const mutation = useMutation({
    mutationFn: () => {
      const selectedLines = returnLines.filter((l) => l.selected && parseFloat(l.qty) > 0);
      if (selectedLines.length === 0) {
        throw new Error("حداقل یک قلم باید انتخاب شود.");
      }
      return api("/workshop/purchase-returns/create_return/", {
        method: "POST",
        body: {
          return_date: returnDate,
          purchase_id: Number(purchaseId),
          reason,
          lines: selectedLines.map((l) => ({
            purchase_line_id: l.purchase_line_id,
            qty: String(l.qty),
          })),
        },
      });
    },
    onSuccess: () => {
      toast.success("برگشت از خرید با موفقیت ثبت شد.");
      qc.invalidateQueries({ queryKey: ["purchase-returns"] });
      qc.invalidateQueries({ queryKey: ["purchases-view"] });
      qc.invalidateQueries({ queryKey: ["purchase-detail"] });
      onOpenChange(false);
      reset();
    },
    onError: (e: unknown) => {
      let msg = "خطا در ثبت برگشت.";
      if (e instanceof ApiError) {
        msg = typeof e.detail === "string" ? e.detail : `خطای HTTP ${e.status}`;
      } else if (e instanceof Error) {
        msg = e.message;
      }
      toast.error(msg);
    },
  });

  const reset = () => {
    setReturnDate(todayISO());
    setPurchaseId("");
    setReason("");
    setReturnLines([]);
  };

  const canSubmit = purchaseId && returnLines.some((l) => l.selected && parseFloat(l.qty) > 0);

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-4xl" dir="rtl">
        <DialogHeader>
          <DialogTitle>برگشت از خرید</DialogTitle>
          <DialogDescription>برگشت کالای خریداری‌شده به تأمین‌کننده</DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>تاریخ برگشت</Label>
            <DatePicker value={returnDate} onChange={setReturnDate} />
          </div>
          <div className="space-y-1.5">
            <Label>فاکتور خرید</Label>
            <Select value={purchaseId} onValueChange={setPurchaseId}>
              <SelectTrigger><SelectValue placeholder="انتخاب فاکتور" /></SelectTrigger>
              <SelectContent>
                {purchases.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.purchase_no} — {p.contractor_name} ({formatDate(p.purchase_date)})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="ret-reason">علت برگشت</Label>
            <Textarea id="ret-reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="مثلاً: کیفیت نامناسب، کسر تعداد، ..." />
          </div>
        </div>

        {purchaseId && returnLines.length > 0 && (
          <div className="space-y-3">
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right w-12">انتخاب</TableHead>
                    <TableHead className="text-right">شرح کالا</TableHead>
                    <TableHead className="text-right">مقدار خرید</TableHead>
                    <TableHead className="text-right">قبلاً برگشت</TableHead>
                    <TableHead className="text-right">قابل برگشت</TableHead>
                    <TableHead className="text-right">مقدار برگشتی</TableHead>
                    <TableHead className="text-right">قیمت واحد</TableHead>
                    <TableHead className="text-right">جمع برگشت</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {returnLines.map((l, idx) => {
                    const lineTotal = parseFloat(l.qty || "0") * parseFloat(l.unit_price || "0");
                    const isFullyReturned = l.max_qty <= 0;
                    return (
                      <TableRow key={idx} className={isFullyReturned ? "bg-red-50/50 dark:bg-red-950/20" : ""}>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={l.selected}
                            disabled={isFullyReturned}
                            onChange={(e) => {
                              setReturnLines((prev) => prev.map((x, i) =>
                                i === idx ? { ...x, selected: e.target.checked } : x
                              ));
                            }}
                            className="h-4 w-4"
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {l.product_name}
                          {isFullyReturned && (
                            <Badge variant="destructive" className="mr-2 text-[10px]">کاملاً برگشت شده</Badge>
                          )}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(parseFloat(l.qty || "0") + l.returned_qty + (l.max_qty > 0 ? parseFloat(l.qty || "0") : 0))}</TableCell>
                        <TableCell className="nums text-red-600" dir="ltr">
                          {l.returned_qty > 0 ? formatNumber(l.returned_qty) : "—"}
                        </TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(l.max_qty)}</TableCell>
                        <TableCell>
                          <Input
                            dir="ltr"
                            className="nums w-24"
                            type="number"
                            min="0"
                            max={l.max_qty}
                            value={l.qty}
                            disabled={!l.selected || isFullyReturned}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value);
                              if (val > l.max_qty) {
                                toast.error(`مقدار برگشتی نمی‌تواند بیشتر از ${l.max_qty} باشد.`);
                                return;
                              }
                              setReturnLines((prev) => prev.map((x, i) =>
                                i === idx ? { ...x, qty: e.target.value } : x
                              ));
                            }}
                          />
                        </TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(parseFloat(l.unit_price || "0"))}</TableCell>
                        <TableCell className="nums font-semibold" dir="ltr">{formatRial(lineTotal)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>

            <div className="flex items-center justify-between rounded-md border bg-muted/30 p-3">
              <div className="text-sm">
                <span className="text-muted-foreground">جمع کل برگشت: </span>
                <span className="font-bold nums">{formatNumber(totalQty)}</span>
                <span className="text-muted-foreground mr-3">معادل </span>
                <span className="font-bold text-primary nums">{formatRial(totalAmount)}</span>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !canSubmit}
          >
            {mutation.isPending ? "در حال ذخیره…" : "ثبت برگشت"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
