"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Play, PackageCheck } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import { MOCK_BATCHES, MOCK_PRODUCTS } from "@/lib/mock-data";
import { formatNumber, formatRial } from "@/lib/format";
import { todayISO, formatDate } from "@/lib/calendar";
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
import { DatePicker } from "@/components/dialogs/datepicker";

type Batch = (typeof MOCK_BATCHES)[number] & { product_name?: string; product_id?: number; };
type Product = (typeof MOCK_PRODUCTS)[number];

interface ProductionBatchDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  batchId?: number | null;
  onBatchCreated?: (id: number) => void;
}

const STEPS = [
  { id: 1, label: "سربرگ بچ" },
  { id: 2, label: "شروع/تکمیل تولید" },
  { id: 3, label: "خروجی و خلاصه" },
];

export function ProductionBatchDialog({ open, onOpenChange, batchId, onBatchCreated }: ProductionBatchDialogProps) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);
  const [productId, setProductId] = React.useState<string>("");
  const [plannedQty, setPlannedQty] = React.useState("100");
  const [notes, setNotes] = React.useState("");
  const [createdBatchId, setCreatedBatchId] = React.useState<number | null>(null);
  const [batchStatus, setBatchStatus] = React.useState<string>("planned");
  const [actualQty, setActualQty] = React.useState("0");
  const [wasteQty, setWasteQty] = React.useState("0");
  const [completionDate, setCompletionDate] = React.useState<string | null>(todayISO());

  const { data: products } = useQuery({
    queryKey: ["products-options"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 200 } }),
  });
  const productList = products?.results ?? MOCK_PRODUCTS;

  // If opened with a specific batch id, pre-load it
  React.useEffect(() => {
    if (batchId) {
      setCreatedBatchId(batchId);
      setStep(2);
      // Fetch the batch status
      api<Batch>(`/production/batches/${batchId}/`).then((b) => {
        setProductId(String(b.product_id ?? b.product?.id ?? ""));
        setPlannedQty(b.planned_qty);
        setNotes(b.notes ?? "");
        setBatchStatus(b.status);
        setActualQty(b.actual_qty && b.actual_qty !== "0" ? b.actual_qty : b.planned_qty);
      }).catch(() => undefined);
    } else {
      setCreatedBatchId(null);
      setStep(1);
      setBatchStatus("planned");
    }
  }, [batchId, open]);

  const createBatch = useMutation({
    mutationFn: () =>
      api<{ id: number; batch_no: string }>("/production/batches/create/", {
        method: "POST",
        body: { product_id: Number(productId), planned_qty: plannedQty, notes },
      }),
    onSuccess: (data) => {
      toast.success("بچ ساخته شد.");
      qc.invalidateQueries({ queryKey: ["batches"] });
      setCreatedBatchId(data.id);
      setBatchStatus("planned");
      onBatchCreated?.(data.id);
      setStep(2);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const startBatch = useMutation({
    mutationFn: () => api(`/production/batches/${createdBatchId}/start/`, { method: "POST" }),
    onSuccess: () => {
      toast.success("تولید آغاز شد.");
      qc.invalidateQueries({ queryKey: ["batches"] });
      setBatchStatus("in_progress");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const completeBatch = useMutation({
    mutationFn: () =>
      api("/production/batches/complete/", {
        method: "POST",
        body: { batch_id: createdBatchId, actual_qty: actualQty, waste_qty: wasteQty, completion_date: completionDate },
      }),
    onSuccess: () => {
      toast.success("بچ با موفقیت تکمیل شد.");
      qc.invalidateQueries({ queryKey: ["batches"] });
      setBatchStatus("completed");
      setStep(3);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const reset = () => {
    setStep(1);
    setProductId("");
    setPlannedQty("100");
    setNotes("");
    setCreatedBatchId(null);
    setBatchStatus("planned");
    setActualQty("0");
    setWasteQty("0");
    setCompletionDate(todayISO());
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>ثبت تولید</DialogTitle>
          <DialogDescription>ساخت، شروع و تکمیل بچ تولید</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2 text-xs">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              <button
                type="button"
                onClick={() => (s.id <= step ? setStep(s.id) : null)}
                className={`flex items-center gap-2 rounded-full border px-3 py-1 ${
                  step === s.id ? "border-primary bg-primary/5 text-primary" : s.id < step ? "text-foreground" : "text-muted-foreground"
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
              <Label>محصول (محصول تمام‌شده)</Label>
              <Select value={productId} onValueChange={setProductId}>
                <SelectTrigger><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                <SelectContent>
                  {productList.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>{p.name} — {p.code}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="b-qty">مقدار برنامه‌ریزی‌شده</Label>
              <Input id="b-qty" type="number" dir="ltr" className="nums" value={plannedQty} onChange={(e) => setPlannedQty(e.target.value)} />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="b-notes">یادداشت</Label>
              <Textarea id="b-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="مثلاً: تولید صبح" />
            </div>
            {createdBatchId && (
              <div className="sm:col-span-2 text-xs text-muted-foreground">
                بچ ساخته‌شده: <span className="font-mono nums">B-#{createdBatchId}</span>
              </div>
            )}
          </div>
        )}

        {step === 2 && createdBatchId && (
          <div className="space-y-4">
            <div className="rounded-md border p-3 text-sm space-y-1">
              <div className="flex justify-between"><span className="text-muted-foreground">بچ</span><span className="font-mono nums">#{createdBatchId}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">محصول</span><span>{productList.find((p) => p.id === Number(productId))?.name ?? "—"}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">مقدار برنامه</span><span className="nums">{formatNumber(plannedQty)}</span></div>
              <div className="flex justify-between"><span className="text-muted-foreground">وضعیت</span><Badge>{batchStatus === "planned" ? "برنامه‌ریزی‌شده" : batchStatus === "in_progress" ? "در حال اجرا" : "تکمیل‌شده"}</Badge></div>
            </div>

            {batchStatus === "planned" && (
              <Button onClick={() => startBatch.mutate()} disabled={startBatch.isPending}>
                <Play className="h-4 w-4" /> شروع تولید
              </Button>
            )}

            {batchStatus === "in_progress" && (
              <div className="space-y-3 rounded-md border p-3">
                <p className="text-sm font-semibold">تکمیل تولید</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="cp-actual">مقدار واقعی</Label>
                    <Input id="cp-actual" type="number" dir="ltr" className="nums" value={actualQty} onChange={(e) => setActualQty(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="cp-waste">مقدار ضایعات</Label>
                    <Input id="cp-waste" type="number" dir="ltr" className="nums" value={wasteQty} onChange={(e) => setWasteQty(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label>تاریخ تکمیل</Label>
                    <DatePicker value={completionDate} onChange={setCompletionDate} />
                  </div>
                </div>
                <Button onClick={() => completeBatch.mutate()} disabled={completeBatch.isPending}>
                  <PackageCheck className="h-4 w-4" /> تکمیل تولید
                </Button>
              </div>
            )}

            {batchStatus === "completed" && (
              <p className="text-sm text-emerald-600">بچ تکمیل‌شده. می‌توانید خروجی محصول را ثبت کنید.</p>
            )}
          </div>
        )}

        {step === 3 && createdBatchId && (
          <div className="space-y-3">
            <div className="rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3 text-sm">
              <p className="font-semibold text-emerald-700 dark:text-emerald-400 mb-2">بچ تکمیل شد ✓</p>
              <div className="grid grid-cols-2 gap-3">
                <div><p className="text-xs text-muted-foreground">مقدار برنامه</p><p className="font-medium nums">{formatNumber(plannedQty)}</p></div>
                <div><p className="text-xs text-muted-foreground">مقدار واقعی</p><p className="font-medium nums">{formatNumber(actualQty)}</p></div>
                <div><p className="text-xs text-muted-foreground">ضایعات</p><p className="font-medium nums">{formatNumber(wasteQty)}</p></div>
                <div><p className="text-xs text-muted-foreground">تاریخ تکمیل</p><p className="font-medium nums" dir="ltr">{formatDate(completionDate)}</p></div>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">لات محصول تمام‌شده در انبار محصول‌های ساخته‌شده ایجاد می‌شود. برای ثبت خروجی، از دکمه «خروج محصول» استفاده کنید.</p>
            </div>
          </div>
        )}

        <DialogFooter className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>بستن</Button>
          <div className="flex items-center gap-2">
            {step === 1 && !createdBatchId && (
              <Button onClick={() => createBatch.mutate()} disabled={createBatch.isPending || !productId}>
                {createBatch.isPending ? "در حال ساخت…" : "ساخت بچ"}
              </Button>
            )}
            {step === 2 && batchStatus === "completed" && (
              <Button onClick={() => setStep(3)}>مشاهده خروجی</Button>
            )}
            {step === 3 && (
              <Button onClick={() => onOpenChange(false)}>پایان</Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
