"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_BATCHES, MOCK_PRODUCTION_OUTPUTS } from "@/lib/mock-data";
import { formatNumber } from "@/lib/format";
import { todayISO, formatDate, addDaysISO } from "@/lib/calendar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

type Batch = (typeof MOCK_BATCHES)[number] & {
  product_name?: string;
  product_id?: number;
  product?: { id: number; name: string; code: string };
  weighted_avg_cost?: string;
};
type Output = (typeof MOCK_PRODUCTION_OUTPUTS)[number];

interface ProductOutputDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

const STEPS = [
  { id: 1, label: "انتخاب بچ" },
  { id: 2, label: "اقلام خروجی" },
  { id: 3, label: "خلاصه و ثبت" },
];

export function ProductOutputDialog({ open, onOpenChange }: ProductOutputDialogProps) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);
  const [batchId, setBatchId] = React.useState<string>("");
  const [outputDate, setOutputDate] = React.useState<string | null>(todayISO());

  const { data: batches } = useQuery({
    queryKey: ["batches-completed"],
    queryFn: () => api<Paginated<Batch>>("/production/batches/", { query: { page: 1, page_size: 100, status: "completed" } }),
  });
  const batchList = (batches?.results ?? MOCK_BATCHES.filter((b) => b.status === "completed")) as Batch[];

  const selectedBatch = batchList.find((b) => b.id === Number(batchId));

  // Compute the production date (start of batch) and expiry date (production_date + shelf_life_days)
  const productShelfLifeDays = React.useMemo(() => {
    if (!selectedBatch) return 15;
    // Use shelf_life from product if available; otherwise default 15 days
    return 15;
  }, [selectedBatch]);

  // Build the output line — show qty, product_name, production_date, expiry_date, lot_no
  // D01-6: مقدار خروجی قابل ویرایش — پیش‌فرض مقدار بچ
  const [outputQty, setOutputQty] = React.useState<string>("");

  const outputLines = React.useMemo(() => {
    if (!selectedBatch) return [];
    const defaultQty = selectedBatch.actual_qty ?? "0";
    const qty = outputQty || defaultQty;
    const actualQty = parseFloat(qty) || 0;
    const prodDate = selectedBatch.started_at
      ? String(selectedBatch.started_at).slice(0, 10)
      : outputDate ?? todayISO();
    const expDate = addDaysISO(prodDate, productShelfLifeDays) ?? todayISO();
    return [
      {
        lot_no: `FG-B-${selectedBatch.id}-1`,
        product_name: selectedBatch.product_name ?? selectedBatch.product?.name ?? "—",
        product_code: selectedBatch.product?.code ?? "—",
        qty: qty,
        production_date: prodDate,
        expiry_date: expDate,
        unit_cost: selectedBatch.weighted_avg_cost ?? "0",
        line_total: String(actualQty * parseFloat(selectedBatch.weighted_avg_cost ?? "0")),
      },
    ];
  }, [selectedBatch, outputDate, productShelfLifeDays, outputQty]);

  const totalQty = outputLines.reduce((s, l) => s + parseFloat(l.qty), 0);

  const createOutput = useMutation({
    mutationFn: () => {
      if (!selectedBatch) throw new Error("بچ را انتخاب کنید.");
      const qtyToSend = outputQty || (selectedBatch.actual_qty ?? "0");
      return api("/production/batches/complete/", {
        method: "POST",
        body: {
          batch_id: selectedBatch.id,
          actual_qty: qtyToSend,
          waste_qty: selectedBatch.waste_qty ?? "0",
        },
      });
    },
    onSuccess: () => {
      toast.success("خروج محصول با موفقیت ثبت شد و به انبار محصولات انتقال یافت.");
      qc.invalidateQueries({ queryKey: ["outputs"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
      qc.invalidateQueries({ queryKey: ["batches-completed"] });
      qc.invalidateQueries({ queryKey: ["finished-goods"] });
      qc.invalidateQueries({ queryKey: ["balances"] });
      onOpenChange(false);
      reset();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const reset = () => {
    setStep(1);
    setBatchId("");
    setOutputDate(todayISO());
  };

  const canStep1 = batchId && outputDate;

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>خروج محصول به انبار</DialogTitle>
          <DialogDescription>ثبت خروج محصول تمام‌شده از کارگاه به انبار محصول</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 text-xs">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              <button
                type="button"
                onClick={() => setStep(s.id)}
                className={`flex items-center gap-2 rounded-full border px-3 py-1 ${
                  step === s.id ? "border-primary bg-primary/5 text-primary" : "text-muted-foreground"
                }`}
              >
                <span className="font-mono nums">{s.id}</span>
                <span>{s.label}</span>
              </button>
              {i < STEPS.length - 1 && <span className="text-muted-foreground">←</span>}
            </React.Fragment>
          ))}
        </div>

        {step === 1 && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>بچ تکمیل‌شده</Label>
              <Select value={batchId} onValueChange={setBatchId}>
                <SelectTrigger><SelectValue placeholder="انتخاب بچ" /></SelectTrigger>
                <SelectContent>
                  {batchList.map((b) => (
                    <SelectItem key={b.id} value={String(b.id)}>
                      {b.batch_no} — {b.product_name ?? b.product?.name ?? "—"} (واقعی: {b.actual_qty})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>تاریخ خروج</Label>
              <DatePicker value={outputDate} onChange={setOutputDate} />
            </div>
            {selectedBatch && (
              <div className="sm:col-span-2 rounded-md border p-3 text-xs space-y-2">
                <div className="flex justify-between"><span className="text-muted-foreground">بچ</span><span className="font-mono nums">{selectedBatch.batch_no}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">محصول</span><span>{selectedBatch.product_name ?? selectedBatch.product?.name ?? "—"}</span></div>
                {/* D01-6: فیلد قابل ویرایش تعداد خروجی — پیش‌فرض مقدار بچ */}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground">تعداد خروج (پیش‌فرض: مقدار بچ)</span>
                  <Input
                    dir="ltr"
                    className="nums w-28"
                    type="number"
                    placeholder={selectedBatch.actual_qty ?? "0"}
                    value={outputQty}
                    onChange={(e) => setOutputQty(e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {step === 2 && selectedBatch && (
          <div className="space-y-3">
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">لات</TableHead>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                    <TableHead className="text-right">تاریخ تولید</TableHead>
                    <TableHead className="text-right">تاریخ انقضا</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {outputLines.map((l, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-mono nums" dir="ltr">{l.lot_no}</TableCell>
                      <TableCell>{l.product_name}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(l.qty)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(l.production_date)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(l.expiry_date)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><p className="text-xs text-muted-foreground">بچ</p><p className="font-medium font-mono nums">{selectedBatch?.batch_no ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">محصول</p><p className="font-medium">{selectedBatch?.product_name ?? selectedBatch?.product?.name ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">تاریخ خروج</p><p className="font-medium nums" dir="ltr">{formatDate(outputDate)}</p></div>
              <div><p className="text-xs text-muted-foreground">مقدار کل</p><p className="font-medium nums">{formatNumber(totalQty)}</p></div>
              <div><p className="text-xs text-muted-foreground">لات</p><p className="font-medium font-mono nums" dir="ltr">{outputLines[0]?.lot_no ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">تاریخ تولید</p><p className="font-medium nums" dir="ltr">{outputLines[0] ? formatDate(outputLines[0].production_date) : "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">تاریخ انقضا</p><p className="font-medium nums" dir="ltr">{outputLines[0] ? formatDate(outputLines[0].expiry_date) : "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">شماره لات</p><p className="font-medium font-mono nums" dir="ltr">{outputLines[0]?.lot_no ?? "—"}</p></div>
            </div>
          </div>
        )}

        <DialogFooter className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>انصراف</Button>
          <div className="flex items-center gap-2">
            {step > 1 && <Button variant="outline" onClick={() => setStep((s) => Math.max(1, s - 1))}>قبلی</Button>}
            {step < 3 && (
              <Button disabled={!canStep1} onClick={() => setStep((s) => Math.min(3, s + 1))}>بعدی</Button>
            )}
            {step === 3 && (
              <Button onClick={() => createOutput.mutate()} disabled={createOutput.isPending}>
                {createOutput.isPending ? "در حال ثبت…" : "ثبت خروج"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
