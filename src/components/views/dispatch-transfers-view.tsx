"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Plus, Check, Truck, ArrowLeftRight, MapPin, Trash2, Users } from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_DISPATCHES, MOCK_TRANSFERS, MOCK_STORES, MOCK_PRODUCTS } from "@/lib/mock-data";
import { formatDate, formatDateTime, formatNumber } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pager, TableSkeleton, EmptyState } from "@/components/common";

type Dispatch = (typeof MOCK_DISPATCHES)[number];
type Transfer = (typeof MOCK_TRANSFERS)[number];
type Store = (typeof MOCK_STORES)[number];
type Product = (typeof MOCK_PRODUCTS)[number];

const DISPATCH_STATUS: Record<string, string> = {
  draft: "پیش‌نویس",
  loading: "بارگذاری",
  pending: "در انتظار",
  in_transit: "در حال حمل",
  in_delivery: "در حال تحویل",
  arrived: "تحویل‌شده",
  delivered: "تحویل‌شده",
  canceled: "لغوشده",
};

const TRANSFER_STATUS: Record<string, string> = {
  pending: "در انتظار",
  approved: "تأییدشده",
  rejected: "رد‌شده",
  completed: "تکمیل‌شده",
  canceled: "لغوشده",
};

function CreateDispatchDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [storeId, setStoreId] = React.useState("");
  const [driver, setDriver] = React.useState("");

  const { data: stores } = useQuery({
    queryKey: ["stores-options-dispatch"],
    queryFn: () => api<Paginated<Store>>("/partners/stores/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () => api("/dispatch/create_dispatch/", { method: "POST", body: { store_id: Number(storeId), driver } }),
    onSuccess: () => {
      toast.success("سند پخش ایجاد شد.");
      qc.invalidateQueries({ queryKey: ["dispatches"] });
      setStoreId("");
      setDriver("");
      onOpenChange(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>سند پخش جدید</DialogTitle>
          <DialogDescription>یک سند پخش برای فروشگاه انتخاب‌شده ایجاد کنید.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>فروشگاه</Label>
            <Select value={storeId} onValueChange={setStoreId}>
              <SelectTrigger><SelectValue placeholder="انتخاب فروشگاه" /></SelectTrigger>
              <SelectContent>
                {stores?.results.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>{s.name} — {s.city}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="d-driver">راننده</Label>
            <Input id="d-driver" value={driver} onChange={(e) => setDriver(e.target.value)} placeholder="نام راننده" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !storeId}>
            {mutation.isPending ? "در حال ایجاد…" : "ایجاد سند"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CreateTransferDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [fromStore, setFromStore] = React.useState("");
  const [toStore, setToStore] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [lines, setLines] = React.useState<Array<{ product_id: string; qty: string }>>([{ product_id: "", qty: "1" }]);

  const { data: stores } = useQuery({
    queryKey: ["stores-options-transfer"],
    queryFn: () => api<Paginated<Store>>("/partners/stores/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });
  const { data: products } = useQuery({
    queryKey: ["products-options-transfer"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const addLine = () => setLines((l) => [...l, { product_id: "", qty: "1" }]);
  const removeLine = (i: number) => setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<{ product_id: string; qty: string }>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const mutation = useMutation({
    mutationFn: () =>
      api("/transfers/create/", {
        method: "POST",
        body: {
          from_store_id: Number(fromStore),
          to_store_id: Number(toStore),
          lines: lines.map((l) => ({ product_id: Number(l.product_id), qty: l.qty })),
          reason,
        },
      }),
    onSuccess: () => {
      toast.success("سند انتقال ایجاد شد.");
      qc.invalidateQueries({ queryKey: ["transfers"] });
      setFromStore("");
      setToStore("");
      setReason("");
      setLines([{ product_id: "", qty: "1" }]);
      onOpenChange(false);
    },
    onError: (e: Error) => {
      let msg = e instanceof Error ? e.message : "خطا در ثبت انتقال.";
      if (e && typeof e === "object" && "detail" in e) {
        const detail = (e as { detail: unknown }).detail;
        if (typeof detail === "string") msg = detail;
        else if (detail && typeof detail === "object") msg = JSON.stringify(detail);
      }
      toast.error(`خطا: ${msg}`);
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>انتقال بین فروشگاه‌ها</DialogTitle>
          <DialogDescription>درخواست انتقال کالا از یک فروشگاه به فروشگاه دیگر</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>فروشگاه مبدأ</Label>
              <Select value={fromStore} onValueChange={setFromStore}>
                <SelectTrigger><SelectValue placeholder="انتخاب فروشگاه" /></SelectTrigger>
                <SelectContent>
                  {stores?.results.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>فروشگاه مقصد</Label>
              <Select value={toStore} onValueChange={setToStore}>
                <SelectTrigger><SelectValue placeholder="انتخاب فروشگاه" /></SelectTrigger>
                <SelectContent>
                  {stores?.results
                    .filter((s) => String(s.id) !== fromStore)
                    .map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>علت انتقال (اختیاری)</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="مثلاً: توزیع مجدد موجودی" />
          </div>

          <div className="rounded-lg border">
            <div className="grid grid-cols-[1fr_120px_40px] gap-2 border-b bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
              <span>محصول</span>
              <span className="text-right">تعداد</span>
              <span />
            </div>
            <div className="max-h-64 overflow-y-auto scroll-pretty">
              {lines.map((l, i) => (
                <div key={i} className="grid grid-cols-[1fr_120px_40px] gap-2 border-b last:border-0 px-3 py-2">
                  <Select value={l.product_id} onValueChange={(v) => updateLine(i, { product_id: v })}>
                    <SelectTrigger className="h-9"><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                    <SelectContent>
                      {products?.results.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input className="h-9 nums" dir="ltr" value={l.qty} onChange={(e) => updateLine(i, { qty: e.target.value })} type="number" min="1" />
                  <Button variant="ghost" size="icon" onClick={() => removeLine(i)} disabled={lines.length === 1} aria-label="حذف خط">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
            <div className="px-3 py-2">
              <Button variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-4 w-4" /> افزودن خط
              </Button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !fromStore || !toStore || fromStore === toStore || lines.some((l) => !l.product_id)}
          >
            {mutation.isPending ? "در حال ثبت…" : "ثبت انتقال"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Waste (ضایعات) — مدیریت اسناد ضایعات فروشگاه/انبار/عامل پخش
// ============================================================================

interface WasteDocument {
  id: number;
  waste_no: string;
  waste_type: string;
  waste_type_display?: string;
  store_id?: number | null;
  store_name?: string;
  warehouse_id?: number | null;
  warehouse_name?: string;
  distributor_id?: number | null;
  distributor_name?: string;
  waste_date: string;
  reason: string;
  total_value: string;
  lines_count: number;
}

const WASTE_TYPE_LABEL: Record<string, string> = {
  store: "فروشگاه",
  warehouse: "انبار",
  distributor: "عامل پخش",
};

const WASTE_CONDITION_LABEL: Record<string, string> = {
  damaged: "آسیب‌دیده",
  expired: "منقضی",
  near_expiry: "نزدیک به انقضا",
  lost: "گم‌شده",
};

function CreateWasteDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [wasteType, setWasteType] = React.useState("warehouse");
  const [storeId, setStoreId] = React.useState("");
  const [warehouseId, setWarehouseId] = React.useState("");
  const [distributorId, setDistributorId] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [lines, setLines] = React.useState<Array<{ product_id: string; qty: string; unit_cost: string; condition: string }>>([{ product_id: "", qty: "1", unit_cost: "25000", condition: "damaged" }]);

  const { data: stores } = useQuery({
    queryKey: ["stores-options-waste"],
    queryFn: () => api<Paginated<Store>>("/partners/stores/", { query: { page: 1, page_size: 100 } }),
    enabled: open && wasteType === "store",
  });
  const { data: distributors } = useQuery({
    queryKey: ["distributors-options-waste"],
    queryFn: () => api<Paginated<any>>("/partners/distributors/", { query: { page: 1, page_size: 100 } }),
    enabled: open && wasteType === "distributor",
  });
  const { data: products } = useQuery({
    queryKey: ["products-options-waste"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const addLine = () => setLines((l) => [...l, { product_id: "", qty: "1", unit_cost: "25000", condition: "damaged" }]);
  const removeLine = (i: number) => setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<{ product_id: string; qty: string; unit_cost: string; condition: string }>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const mutation = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {
        waste_type: wasteType,
        lines: lines.map((l) => ({
          product_id: Number(l.product_id),
          qty: l.qty,
          unit_cost: l.unit_cost,
          condition: l.condition,
        })),
        reason,
      };
      if (wasteType === "store") body.store_id = Number(storeId);
      if (wasteType === "distributor") body.distributor_id = Number(distributorId);
      return api("/inventory/wastes/create_waste/", { method: "POST", body });
    },
    onSuccess: () => {
      toast.success("سند ضایعات ثبت شد.");
      qc.invalidateQueries({ queryKey: ["wastes"] });
      setReason("");
      setStoreId("");
      setDistributorId("");
      setLines([{ product_id: "", qty: "1", unit_cost: "25000", condition: "damaged" }]);
      onOpenChange(false);
    },
    onError: (e: Error) => {
      let msg = e instanceof Error ? e.message : "خطا در ثبت ضایعات.";
      if (e && typeof e === "object" && "detail" in e) {
        const detail = (e as { detail: unknown }).detail;
        if (typeof detail === "string") msg = detail;
        else if (detail && typeof detail === "object") msg = JSON.stringify(detail);
      }
      toast.error(`خطا: ${msg}`);
    },
  });

  // اعتبارسنجی: اگه store انتخاب شده ولی storeId خالیه، یا distributor
  const isValid = (() => {
    if (wasteType === "store" && !storeId) return false;
    if (wasteType === "distributor" && !distributorId) return false;
    if (lines.some((l) => !l.product_id)) return false;
    return true;
  })();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>سند ضایعات</DialogTitle>
          <DialogDescription>ثبت کالاهای ضایع‌شده در فروشگاه/انبار/عامل پخش</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>نوع ضایعات</Label>
              <Select value={wasteType} onValueChange={setWasteType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(WASTE_TYPE_LABEL).map(([v, label]) => (
                    <SelectItem key={v} value={v}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              {wasteType === "store" && (
                <>
                  <Label>فروشگاه</Label>
                  <Select value={storeId} onValueChange={setStoreId}>
                    <SelectTrigger><SelectValue placeholder="انتخاب فروشگاه" /></SelectTrigger>
                    <SelectContent>
                      {stores?.results.map((s) => (
                        <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </>
              )}
              {wasteType === "distributor" && (
                <>
                  <Label>عامل پخش</Label>
                  <Select value={distributorId} onValueChange={setDistributorId}>
                    <SelectTrigger><SelectValue placeholder="انتخاب عامل پخش" /></SelectTrigger>
                    <SelectContent>
                      {distributors?.results.map((d: any) => (
                        <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </>
              )}
              {wasteType === "warehouse" && (
                <div>
                  <Label>انبار اصلی</Label>
                  <p className="text-xs text-muted-foreground mt-2">انبار اصلی به‌صورت خودکار انتخاب می‌شود</p>
                </div>
              )}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>علت (اختیاری)</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="مثلاً: کالا آسیب‌دیده" />
          </div>

          <div className="rounded-lg border">
            <div className="grid grid-cols-[1fr_90px_120px_120px_40px] gap-2 border-b bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
              <span>محصول</span>
              <span className="text-right">تعداد</span>
              <span className="text-right">بهای واحد</span>
              <span className="text-right">وضعیت</span>
              <span />
            </div>
            <div className="max-h-64 overflow-y-auto scroll-pretty">
              {lines.map((l, i) => (
                <div key={i} className="grid grid-cols-[1fr_90px_120px_120px_40px] gap-2 border-b last:border-0 px-3 py-2">
                  <Select value={l.product_id} onValueChange={(v) => updateLine(i, { product_id: v })}>
                    <SelectTrigger className="h-9"><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                    <SelectContent>
                      {products?.results.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input className="h-9 nums" dir="ltr" value={l.qty} onChange={(e) => updateLine(i, { qty: e.target.value })} type="number" min="1" />
                  <Input className="h-9 nums" dir="ltr" value={l.unit_cost} onChange={(e) => updateLine(i, { unit_cost: e.target.value })} type="number" min="0" />
                  <Select value={l.condition} onValueChange={(v) => updateLine(i, { condition: v })}>
                    <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {Object.entries(WASTE_CONDITION_LABEL).map(([v, label]) => (
                        <SelectItem key={v} value={v}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" onClick={() => removeLine(i)} disabled={lines.length === 1} aria-label="حذف خط">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
            <div className="px-3 py-2">
              <Button variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-4 w-4" /> افزودن خط
              </Button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !isValid}>
            {mutation.isPending ? "در حال ثبت…" : "ثبت ضایعات"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function WasteTab() {
  const [page, setPage] = React.useState(1);
  const [createOpen, setCreateOpen] = React.useState(false);
  const pageSize = 10;
  const { data, isLoading } = useQuery({
    queryKey: ["wastes", { page, page_size: pageSize }],
    queryFn: () => api<Paginated<WasteDocument>>("/inventory/wastes/", { query: { page, page_size: pageSize } }),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>اسناد ضایعات</CardTitle>
          <CardDescription>ضایعات فروشگاه/انبار/عامل پخش</CardDescription>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          سند ضایعات جدید
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">شماره</TableHead>
                <TableHead className="text-right">نوع</TableHead>
                <TableHead className="text-right">مربوط به</TableHead>
                <TableHead className="text-right">تعداد خطوط</TableHead>
                <TableHead className="text-right">ارزش کل</TableHead>
                <TableHead className="text-right">علت</TableHead>
                <TableHead className="text-right">تاریخ</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={7} className="p-0"><TableSkeleton rows={8} cols={7} /></TableCell></TableRow>
              ) : rows.length === 0 ? (
                <TableRow><TableCell colSpan={7}><EmptyState description="سند ضایعاتی یافت نشد." /></TableCell></TableRow>
              ) : (
                rows.map((w: any) => (
                  <TableRow key={w.id}>
                    <TableCell className="font-mono nums" dir="ltr">{w.waste_no ?? "—"}</TableCell>
                    <TableCell><Badge variant="secondary">{WASTE_TYPE_LABEL[w.waste_type] ?? w.waste_type_display ?? w.waste_type}</Badge></TableCell>
                    <TableCell className="font-medium">
                      {w.warehouse_name ?? w.store_name ?? w.distributor_name ?? "—"}
                    </TableCell>
                    <TableCell className="nums" dir="ltr">{w.lines_count ?? 0}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(w.total_value ?? "0")}</TableCell>
                    <TableCell className="max-w-xs truncate">{w.reason || "—"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground" dir="ltr">{formatDate(w.waste_date)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        <Pager page={page} pageSize={pageSize} count={data?.count ?? 0} onPage={setPage} />
      </CardContent>
      <CreateWasteDialog open={createOpen} onOpenChange={setCreateOpen} />
    </Card>
  );
}

// ============================================================================
// Distributors (عوامل پخش) — مدیریت و وضعیت مالی
// ============================================================================

interface DistributorStatus {
  id?: number;
  distributor_id: number;
  distributor_name: string;
  distributor_code: string;
  mobile: string;
  commission_rate: string;
  total_delivered_value: string;
  total_sold_value: string;
  total_returned_value: string;
  commission_owed: string;
  balance: string;
  store_count: number;
  is_active: boolean;
}

function DistributorStatusTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["distributors-status"],
    queryFn: () => api<{ count: number; results: DistributorStatus[] }>("/partners/distributors/status/"),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <CardHeader>
        <CardTitle>وضعیت عوامل پخش</CardTitle>
        <CardDescription>مبلغ تحویلی، فروش، برگشتی، پورسانت و موجودی طلبکار/بدهکار هر عامل</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">کد</TableHead>
                <TableHead className="text-right">نام</TableHead>
                <TableHead className="text-right">موبایل</TableHead>
                <TableHead className="text-right">فروشگاه‌ها</TableHead>
                <TableHead className="text-right">تحویلی</TableHead>
                <TableHead className="text-right">فروخته‌شده</TableHead>
                <TableHead className="text-right">برگشتی</TableHead>
                <TableHead className="text-right">پورسانت %</TableHead>
                <TableHead className="text-right">پورسانت قابل پرداخت</TableHead>
                <TableHead className="text-right">مانده</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={10} className="p-0"><TableSkeleton rows={5} cols={10} /></TableCell></TableRow>
              ) : rows.length === 0 ? (
                <TableRow><TableCell colSpan={10}><EmptyState description="عاملی پخشی یافت نشد." /></TableCell></TableRow>
              ) : (
                rows.map((d: any) => (
                  <TableRow key={d.distributor_id ?? d.id}>
                    <TableCell className="font-mono nums" dir="ltr">{d.distributor_code ?? "—"}</TableCell>
                    <TableCell className="font-medium">{d.distributor_name ?? "—"}</TableCell>
                    <TableCell className="font-mono nums" dir="ltr">{d.mobile ?? "—"}</TableCell>
                    <TableCell className="nums" dir="ltr">{d.store_count ?? 0}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(d.total_delivered_value ?? "0")}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(d.total_sold_value ?? "0")}</TableCell>
                    <TableCell className="nums text-muted-foreground" dir="ltr">{formatNumber(d.total_returned_value ?? "0")}</TableCell>
                    <TableCell className="nums" dir="ltr">{d.commission_rate ?? "0"}%</TableCell>
                    <TableCell className="nums font-semibold text-emerald-600 dark:text-emerald-400" dir="ltr">{formatNumber(d.commission_owed ?? "0")}</TableCell>
                    <TableCell className="nums font-bold" dir="ltr">{formatNumber(d.balance ?? "0")}</TableCell>
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

function DispatchTab() {
  const [page, setPage] = React.useState(1);
  const [createOpen, setCreateOpen] = React.useState(false);
  const pageSize = 10;
  const { data, isLoading } = useQuery({
    queryKey: ["dispatches", { page, page_size: pageSize }],
    queryFn: () => api<Paginated<Dispatch>>("/dispatch/", { query: { page, page_size: pageSize } }),
  });
  const rows = data?.results ?? [];
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><Truck className="h-5 w-5" /> سندهای پخش</CardTitle>
          <CardDescription>مدیریت توزیع کالا به فروشگاه‌ها</CardDescription>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          پخش جدید
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">شماره</TableHead>
                <TableHead className="text-right">فروشگاه</TableHead>
                <TableHead className="text-right">راننده</TableHead>
                <TableHead className="text-right">مقدار کل</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right">تاریخ</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={8} cols={6} /></TableCell></TableRow>
              ) : rows.length === 0 ? (
                <TableRow><TableCell colSpan={6}><EmptyState /></TableCell></TableRow>
              ) : (
                rows.map((d: any) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono nums" dir="ltr">{d.dispatch_no ?? d.dispatch_number ?? "—"}</TableCell>
                    <TableCell className="font-medium">{d.distributor_name ?? d.store?.name ?? d.store_name ?? "—"}</TableCell>
                    <TableCell>{d.vehicle_plate ?? d.driver ?? "—"}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(d.total_qty ?? "0")}</TableCell>
                    <TableCell><Badge variant="secondary">{DISPATCH_STATUS[d.status] ?? d.status}</Badge></TableCell>
                    <TableCell className="text-xs text-muted-foreground" dir="ltr">{formatDateTime(d.created_at)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        <Pager page={page} pageSize={pageSize} count={data?.count ?? 0} onPage={setPage} />
      </CardContent>
      <CreateDispatchDialog open={createOpen} onOpenChange={setCreateOpen} />
    </Card>
  );
}

function TransferTab() {
  const qc = useQueryClient();
  const [page, setPage] = React.useState(1);
  const [createOpen, setCreateOpen] = React.useState(false);
  const pageSize = 10;
  const { data, isLoading } = useQuery({
    queryKey: ["transfers", { page, page_size: pageSize }],
    queryFn: () => api<Paginated<Transfer>>("/transfers/", { query: { page, page_size: pageSize } }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => api(`/transfers/${id}/approve/`, { method: "POST" }),
    onSuccess: () => {
      toast.success("انتقال تأیید شد.");
      qc.invalidateQueries({ queryKey: ["transfers"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const rows = data?.results ?? [];
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><ArrowLeftRight className="h-5 w-5" /> سندهای انتقال</CardTitle>
          <CardDescription>انتقال کالا بین انبارها</CardDescription>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          انتقال جدید
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">شماره</TableHead>
                <TableHead className="text-right">مبدأ</TableHead>
                <TableHead className="text-right">مقصد</TableHead>
                <TableHead className="text-right">مقدار کل</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right">تاریخ</TableHead>
                <TableHead className="text-right w-24">عملیات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={7} className="p-0"><TableSkeleton rows={8} cols={7} /></TableCell></TableRow>
              ) : rows.length === 0 ? (
                <TableRow><TableCell colSpan={7}><EmptyState /></TableCell></TableRow>
              ) : (
                rows.map((t: any) => {
                  const transferQty = t.total_qty ?? t.lines_count ?? "—";
                  return (
                  <TableRow key={t.id}>
                    <TableCell className="font-mono nums" dir="ltr">{t.transfer_no ?? t.transfer_number ?? "—"}</TableCell>
                    <TableCell>{(t as any).from_store_name ?? (t as any).from_store?.name ?? "—"}</TableCell>
                    <TableCell>{(t as any).to_store_name ?? (t as any).to_store?.name ?? "—"}</TableCell>
                    <TableCell className="nums" dir="ltr">{formatNumber(transferQty)}</TableCell>
                    <TableCell><Badge variant="secondary">{TRANSFER_STATUS[t.status] ?? t.status}</Badge></TableCell>
                    <TableCell className="text-xs text-muted-foreground" dir="ltr">{formatDateTime(t.created_at)}</TableCell>
                    <TableCell>
                      {t.status === "pending" ? (
                        <Button size="sm" variant="outline" onClick={() => approveMutation.mutate(t.id)} disabled={approveMutation.isPending}>
                          <Check className="h-4 w-4" />
                          تأیید
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
        <Pager page={page} pageSize={pageSize} count={data?.count ?? 0} onPage={setPage} />
      </CardContent>
      <CreateTransferDialog open={createOpen} onOpenChange={setCreateOpen} />
    </Card>
  );
}

function StoresGeoCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["stores-geo"],
    queryFn: () => api<any>("/partners/stores/geo_points/"),
  });
  const stores: Store[] = React.useMemo(() => {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    return [];
  }, [data]);
  const minLat = Math.min(...stores.map((s) => s.lat), 35.5);
  const maxLat = Math.max(...stores.map((s) => s.lat), 35.9);
  const minLng = Math.min(...stores.map((s) => s.lng), 51.2);
  const maxLng = Math.max(...stores.map((s) => s.lng), 51.6);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><MapPin className="h-5 w-5" /> نقشه جغرافیایی فروشگاه‌ها</CardTitle>
        <CardDescription>موقعیت تقریبی فروشگاه‌ها بر روی شبکه</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative aspect-[16/9] w-full overflow-hidden rounded-lg border bg-accent/30">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">در حال بارگذاری…</div>
          ) : stores.length === 0 ? (
            <EmptyState />
          ) : (
            stores.map((s) => {
              const x = ((s.lng - minLng) / (maxLng - minLng || 1)) * 90 + 5;
              const y = 90 - ((s.lat - minLat) / (maxLat - minLat || 1)) * 80 - 5;
              return (
                <div
                  key={s.id}
                  className="absolute -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${x}%`, top: `${y}%` }}
                  title={`${s.name} — ${s.city}`}
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md">
                    <MapPin className="h-3 w-3" />
                  </div>
                  <span className="absolute top-6 right-1/2 translate-x-1/2 whitespace-nowrap rounded bg-background/90 px-1.5 py-0.5 text-[10px] shadow">
                    {s.name}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function DispatchTransfersView() {
  return (
    <div className="space-y-4">
      <Tabs defaultValue="dispatch">
        <TabsList>
          <TabsTrigger value="dispatch"><Truck className="h-4 w-4" /> پخش</TabsTrigger>
          <TabsTrigger value="transfers"><ArrowLeftRight className="h-4 w-4" /> انتقال</TabsTrigger>
          <TabsTrigger value="wastes"><Trash2 className="h-4 w-4" /> ضایعات</TabsTrigger>
          <TabsTrigger value="distributors"><Users className="h-4 w-4" /> عوامل پخش</TabsTrigger>
          <TabsTrigger value="stores"><MapPin className="h-4 w-4" /> فروشگاه‌ها</TabsTrigger>
        </TabsList>
        <TabsContent value="dispatch" className="mt-4"><DispatchTab /></TabsContent>
        <TabsContent value="transfers" className="mt-4"><TransferTab /></TabsContent>
        <TabsContent value="wastes" className="mt-4"><WasteTab /></TabsContent>
        <TabsContent value="distributors" className="mt-4"><DistributorStatusTab /></TabsContent>
        <TabsContent value="stores" className="mt-4"><StoresGeoCard /></TabsContent>
      </Tabs>
    </div>
  );
}
