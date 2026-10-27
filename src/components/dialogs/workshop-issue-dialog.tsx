"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2, Layers } from "lucide-react";
import { api, type Paginated } from "@/lib/api";
import {
  MOCK_CONTRACTORS,
  MOCK_EMPLOYEES,
  MOCK_WAREHOUSES,
  MOCK_PRODUCTS,
  MOCK_WORKSHOP_ISSUES,
} from "@/lib/mock-data";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DatePicker } from "@/components/dialogs/datepicker";

type Contractor = (typeof MOCK_CONTRACTORS)[number];
type Employee = (typeof MOCK_EMPLOYEES)[number] & {
  workshop?: number | null;
  workshop_name?: string;
};
type Warehouse = (typeof MOCK_WAREHOUSES)[number];
type Product = (typeof MOCK_PRODUCTS)[number];

interface IssueLine {
  product_id: number | null;
  qty_requested: string;
  allocated_lots?: Array<{ lot_id: number; lot_no: string; qty: string }>;
}

interface WorkshopIssueDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

const STEPS = [
  { id: 1, label: "سربرگ حواله" },
  { id: 2, label: "اقلام و تخصیص FEFO" },
  { id: 3, label: "خلاصه و صدور" },
];

export function WorkshopIssueDialog({ open, onOpenChange }: WorkshopIssueDialogProps) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);
  const [issueDate, setIssueDate] = React.useState<string | null>(todayISO());
  const [employeeId, setEmployeeId] = React.useState<string>("");
  const [fromWarehouseId, setFromWarehouseId] = React.useState<string>("");
  const [toWarehouseId, setToWarehouseId] = React.useState<string>("");
  const [batch, setBatch] = React.useState<string>("");
  const [notes, setNotes] = React.useState("");
  const [lines, setLines] = React.useState<IssueLine[]>([
    { product_id: null, qty_requested: "0" },
  ]);

  // R8 — fetch employees instead of contractors
  const { data: employeesData } = useQuery({
    queryKey: ["employees-options"],
    queryFn: () => api<Paginated<Employee>>("/workshop/employees/", { query: { page: 1, page_size: 100 } }),
  });
  // Also keep contractors query for backward-compat fallback (in case no employees exist)
  const { data: contractors } = useQuery({
    queryKey: ["contractors-options"],
    queryFn: () => api<Paginated<Contractor>>("/workshop/contractors/", { query: { page: 1, page_size: 100 } }),
  });
  // R9 — fetch warehouses filtered by type=raw_materials for source, type=workshop for destination
  const { data: rawWhData } = useQuery({
    queryKey: ["warehouses-raw-materials"],
    queryFn: () => api<Paginated<Warehouse>>("/inventory/warehouses/", { query: { page: 1, page_size: 100, type: "raw_materials" } }),
  });
  const { data: workshopWhData } = useQuery({
    queryKey: ["warehouses-workshop"],
    queryFn: () => api<Paginated<Warehouse>>("/inventory/warehouses/", { query: { page: 1, page_size: 100, type: "workshop" } }),
  });
  // Fetch lots for the selected raw_materials warehouse to know which products are in stock
  const { data: stockBalances } = useQuery({
    queryKey: ["stock-balances-raw", fromWarehouseId],
    queryFn: () => api<Paginated<any>>("/inventory/balances/", { query: { page: 1, page_size: 200, warehouse: fromWarehouseId || undefined } }),
    enabled: !!fromWarehouseId,
  });
  const { data: products } = useQuery({
    queryKey: ["products-options"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 200 } }),
  });

  const employeeList = employeesData?.results ?? MOCK_EMPLOYEES;
  const contractorList = contractors?.results ?? MOCK_CONTRACTORS;
  const rawWarehouses = rawWhData?.results ?? MOCK_WAREHOUSES.filter((w) => w.type === "raw_materials");
  const workshopWarehouses = workshopWhData?.results ?? MOCK_WAREHOUSES.filter((w) => w.type === "workshop");
  const productList = products?.results ?? MOCK_PRODUCTS;
  // Map of in-stock product_id → total_qty (filtered by from-warehouse)
  const inStockMap = React.useMemo(() => {
    const m = new Map<number, number>();
    (stockBalances?.results ?? []).forEach((b: any) => {
      const pid = b.product_id ?? b.product?.id;
      const q = parseFloat(b.total_qty ?? "0");
      if (pid !== undefined && q > 0) m.set(pid, q);
    });
    return m;
  }, [stockBalances]);

  // Filter productList to only those with available stock in the raw-materials warehouse
  const availableProducts = React.useMemo(() => {
    if (inStockMap.size === 0) return productList;
    return productList.filter((p) => inStockMap.has(p.id));
  }, [productList, inStockMap]);

  const totalQty = lines.reduce((s, l) => s + parseFloat(l.qty_requested || "0"), 0);

  const allocateFefo = useMutation({
    mutationFn: (lineIdx: number) => {
      const line = lines[lineIdx];
      if (!line.product_id) throw new Error("محصول را انتخاب کنید.");
      return api("/inventory/allocate-fefo/", {
        method: "POST",
        body: { product_id: line.product_id, qty: line.qty_requested, warehouse_id: Number(fromWarehouseId) },
      });
    },
    onSuccess: (data: any, lineIdx) => {
      toast.success("تخصیص FEFO با موفقیت انجام شد.");
      setLines((prev) => prev.map((l, i) => (i === lineIdx ? { ...l, allocated_lots: data.lots ?? [] } : l)));
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const createIssue = useMutation({
    mutationFn: () => {
      // Resolve contractor from employee's workshop if possible
      const employee = employeeList.find((e) => e.id === Number(employeeId));
      const contractor = employee?.workshop
        ? contractorList.find((c) => c.id === employee.workshop)
        : contractorList[0];
      return api("/workshop/issues/create_issue/", {
        method: "POST",
        body: {
          issue_date: issueDate,
          employee_id: Number(employeeId) || undefined,
          contractor_id: contractor?.id,
          from_warehouse: Number(fromWarehouseId),
          to_warehouse: Number(toWarehouseId),
          production_batch: batch || null,
          notes,
          lines: lines
            .filter((l) => l.product_id !== null)
            .map((l) => ({ product_id: l.product_id, qty: l.qty_requested })),
        },
      });
    },
    onSuccess: () => {
      toast.success("حواله صادر شد.");
      qc.invalidateQueries({ queryKey: ["workshop-issues"] });
      onOpenChange(false);
      reset();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const reset = () => {
    setStep(1);
    setIssueDate(todayISO());
    setEmployeeId("");
    setFromWarehouseId("");
    setToWarehouseId("");
    setBatch("");
    setNotes("");
    setLines([{ product_id: null, qty_requested: "0" }]);
  };

  const canStep1 = issueDate && employeeId && fromWarehouseId && toWarehouseId;
  const canStep2 = lines.length > 0 && lines.every((l) => l.product_id !== null && parseFloat(l.qty_requested) > 0);

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>حواله به کارگاه</DialogTitle>
          <DialogDescription>صدور حواله مواد اولیه از انبار اصلی به کارگاه</DialogDescription>
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
            <div className="space-y-1.5 sm:col-span-2">
              <Label>تاریخ حواله</Label>
              <DatePicker value={issueDate} onChange={setIssueDate} />
            </div>
            {/* R8 — شخص تحویل‌گیرنده (Employee) */}
            <div className="space-y-1.5">
              <Label>شخص تحویل‌گیرنده</Label>
              <Select value={employeeId} onValueChange={setEmployeeId}>
                <SelectTrigger><SelectValue placeholder="انتخاب کارکنان" /></SelectTrigger>
                <SelectContent>
                  {employeeList.length > 0 ? (
                    employeeList.map((e) => (
                      <SelectItem key={e.id} value={String(e.id)}>
                        {(e as any).full_name ?? `${e.first_name ?? ""} ${e.last_name ?? ""}`.trim()} — {(e as any).position ?? ""}
                      </SelectItem>
                    ))
                  ) : (
                    // Fallback: show contractors if no employees
                    contractorList.map((c) => (
                      <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>بچ تولید (اختیاری)</Label>
              <Input value={batch} onChange={(e) => setBatch(e.target.value)} placeholder="B-244" dir="ltr" className="nums" />
            </div>
            {/* R8 — انبار مبدأ (raw_materials فقط) */}
            <div className="space-y-1.5">
              <Label>انبار مبدأ (مواد اولیه)</Label>
              <Select value={fromWarehouseId} onValueChange={setFromWarehouseId}>
                <SelectTrigger><SelectValue placeholder="انتخاب انبار مواد اولیه" /></SelectTrigger>
                <SelectContent>
                  {rawWarehouses.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* R9 — کارگاه مقصد (workshop فقط) */}
            <div className="space-y-1.5">
              <Label>کارگاه مقصد</Label>
              <Select value={toWarehouseId} onValueChange={setToWarehouseId}>
                <SelectTrigger><SelectValue placeholder="انتخاب کارگاه مقصد" /></SelectTrigger>
                <SelectContent>
                  {workshopWarehouses.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="iss-notes">توضیحات</Label>
              <Textarea id="iss-notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="مثلاً: حواله بچ صبح" />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              فقط محصولاتی نمایش داده می‌شوند که در انبار مواد اولیه موجودی دارند.
              {fromWarehouseId && (
                <span> موجودی در «{rawWarehouses.find((w) => w.id === Number(fromWarehouseId))?.name ?? "—"}»</span>
              )}
            </p>
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">موجودی</TableHead>
                    <TableHead className="text-right">مقدار درخواست</TableHead>
                    <TableHead className="text-right">لات‌های تخصیص‌یافته (FEFO)</TableHead>
                    <TableHead className="text-right w-12"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((l, idx) => {
                    const available = (l.product_id ? inStockMap.get(l.product_id) : undefined) ?? null;
                    return (
                      <TableRow key={idx}>
                        <TableCell>
                          <Select
                            value={l.product_id ? String(l.product_id) : ""}
                            onValueChange={(v) => updateLine(idx, { product_id: Number(v) })}
                          >
                            <SelectTrigger className="w-44"><SelectValue placeholder="محصول" /></SelectTrigger>
                            <SelectContent>
                              {availableProducts.map((p) => (
                                <SelectItem key={p.id} value={String(p.id)}>
                                  {p.name} — {p.code}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-xs nums font-mono" dir="ltr">
                          {available !== null ? formatNumber(available) : "—"}
                        </TableCell>
                        <TableCell>
                          <Input dir="ltr" className="nums w-24" type="number" value={l.qty_requested} onChange={(e) => updateLine(idx, { qty_requested: e.target.value })} />
                        </TableCell>
                        <TableCell className="text-xs">
                          {l.allocated_lots && l.allocated_lots.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {l.allocated_lots.map((lot) => (
                                <Badge key={lot.lot_id} variant="outline" className="font-mono nums">
                                  {lot.lot_no ?? `L-${lot.lot_id}`}: {lot.qty}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <Button variant="ghost" size="sm" onClick={() => allocateFefo.mutate(idx)} disabled={allocateFefo.isPending || !l.product_id || !fromWarehouseId}>
                              <Layers className="h-4 w-4" /> تخصیص FEFO
                            </Button>
                          )}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="icon" onClick={() => removeLine(idx)} disabled={lines.length === 1}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            <Button variant="outline" onClick={addLine}>
              <Plus className="h-4 w-4" /> افزودن قلم
            </Button>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><p className="text-xs text-muted-foreground">تاریخ</p><p className="font-medium nums" dir="ltr">{formatDate(issueDate)}</p></div>
              <div>
                <p className="text-xs text-muted-foreground">شخص تحویل‌گیرنده</p>
                <p className="font-medium">
                  {(() => {
                    const e = employeeList.find((x) => x.id === Number(employeeId));
                    if (!e) return "—";
                    return (e as any).full_name ?? `${e.first_name ?? ""} ${e.last_name ?? ""}`.trim();
                  })()}
                </p>
              </div>
              <div><p className="text-xs text-muted-foreground">مبدأ</p><p className="font-medium">{rawWarehouses.find((w) => w.id === Number(fromWarehouseId))?.name ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">کارگاه مقصد</p><p className="font-medium">{workshopWarehouses.find((w) => w.id === Number(toWarehouseId))?.name ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">مقدار کل</p><p className="font-medium nums">{formatNumber(totalQty)}</p></div>
              <div><p className="text-xs text-muted-foreground">تعداد اقلام</p><p className="font-medium nums">{lines.length}</p></div>
            </div>
          </div>
        )}

        <DialogFooter className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => onOpenChange(false)}>انصراف</Button>
          <div className="flex items-center gap-2">
            {step > 1 && <Button variant="outline" onClick={() => setStep((s) => Math.max(1, s - 1))}>قبلی</Button>}
            {step < 3 && (
              <Button disabled={step === 1 ? !canStep1 : !canStep2} onClick={() => setStep((s) => Math.min(3, s + 1))}>
                بعدی
              </Button>
            )}
            {step === 3 && (
              <Button onClick={() => createIssue.mutate()} disabled={createIssue.isPending || !canStep2}>
                {createIssue.isPending ? "در حال صدور…" : "صدور حواله"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  function updateLine(idx: number, patch: Partial<IssueLine>) {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }
  function addLine() {
    setLines((prev) => [...prev, { product_id: null, qty_requested: "0" }]);
  }
  function removeLine(idx: number) {
    setLines((prev) => prev.filter((_, i) => i !== idx));
  }
}
