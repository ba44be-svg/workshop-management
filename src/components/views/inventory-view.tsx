"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Layers, AlertTriangle, Boxes, Wand2 } from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_LOTS, MOCK_STOCK_BALANCE, MOCK_PRODUCTS } from "@/lib/mock-data";
import { formatDate, formatNumber, daysUntil } from "@/lib/format";
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

type Lot = (typeof MOCK_LOTS)[number];
type Balance = (typeof MOCK_STOCK_BALANCE)[number];
type Product = (typeof MOCK_PRODUCTS)[number];

function expiryTone(d: string): { cls: string; label: string } {
  const days = daysUntil(d);
  if (days === null) return { cls: "text-muted-foreground", label: "—" };
  if (days < 0) return { cls: "text-rose-600 dark:text-rose-400 font-semibold", label: "منقضی" };
  if (days <= 3) return { cls: "text-rose-600 dark:text-rose-400 font-semibold", label: `${days} روز` };
  if (days <= 7) return { cls: "text-amber-600 dark:text-amber-400 font-semibold", label: `${days} روز` };
  if (days <= 14) return { cls: "text-yellow-600 dark:text-yellow-400 font-semibold", label: `${days} روز` };
  return { cls: "text-emerald-600 dark:text-emerald-400", label: `${days} روز` };
}

function AllocateFefoDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [productId, setProductId] = React.useState("");
  const [warehouseId, setWarehouseId] = React.useState("1");
  const [qty, setQty] = React.useState("30");
  const [result, setResult] = React.useState<{ lots: Array<{ lot_id: number; qty: string }> } | null>(null);

  const { data: products } = useQuery({
    queryKey: ["products-options-inv"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () =>
      api<{ product_id: number; allocated_qty: string; lots: Array<{ lot_id: number; qty: string }> }>(
        "/inventory/allocate-fefo/",
        { method: "POST", body: { product_id: Number(productId), warehouse_id: Number(warehouseId), qty } }
      ),
    onSuccess: (res) => {
      toast.success("تخصیص FEFO با موفقیت انجام شد.");
      setResult(res);
      qc.invalidateQueries({ queryKey: ["lots"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const close = () => {
    onOpenChange(false);
    setResult(null);
    setProductId("");
    setQty("30");
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && close()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>تخصیص FEFO</DialogTitle>
          <DialogDescription>تخصیص موجودی بر اساس اولین انقضا، اولین خروج.</DialogDescription>
        </DialogHeader>
        {result ? (
          <div className="space-y-3">
            <p className="text-sm">مقدار تخصیص‌یافته: <span className="font-semibold nums">{(result as any).allocated_qty ?? "—"}</span></p>
            <div className="rounded-lg border overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">لات</TableHead>
                    <TableHead className="text-right">مقدار</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.lots.map((l, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-mono nums" dir="ltr">L-{l.lot_id}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(l.qty)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>محصول</Label>
              <Select value={productId} onValueChange={setProductId}>
                <SelectTrigger><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                <SelectContent>
                  {products?.results.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>انبار</Label>
              <Select value={warehouseId} onValueChange={setWarehouseId}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">انبار ۱</SelectItem>
                  <SelectItem value="2">انبار ۲</SelectItem>
                  <SelectItem value="3">انبار ۳</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="a-qty">مقدار موردنیاز</Label>
              <Input id="a-qty" type="number" dir="ltr" className="nums" value={qty} onChange={(e) => setQty(e.target.value)} />
            </div>
          </div>
        )}
        <DialogFooter>
          {result ? (
            <Button onClick={close}>بستن</Button>
          ) : (
            <>
              <Button variant="outline" onClick={close}>انصراف</Button>
              <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !productId}>
                {mutation.isPending ? "در حال تخصیص…" : "تخصیص FEFO"}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function StockBalanceTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["stock-balance"],
    queryFn: () => api<Paginated<Balance>>("/inventory/balances/", { query: { page: 1, page_size: 50 } }),
  });
  const rawRows = data?.results ?? [];

  // پشتیبانی از دو ساختار:
  // - mock: هر ردیف شامل warehouses: [{warehouse_id, warehouse_name, qty}]
  // - backend واقعی: هر ردیف مربوط به یک (product×warehouse) است و warehouses ندارد
  const isMocked = rawRows.length > 0 && Array.isArray((rawRows[0] as any).warehouses);

  type GroupedWarehouse = { warehouse_id: number; warehouse_name: string; qty: string };
  type GroupedRow = {
    product_id: number;
    product_name: string;
    product_code: string;
    total_qty: string;
    warehouses: GroupedWarehouse[];
  };

  const rows: GroupedRow[] = React.useMemo(() => {
    if (isMocked) {
      return rawRows.map((b: any) => ({
        product_id: b.product_id,
        product_name: b.product?.name ?? "—",
        product_code: b.product?.code ?? "—",
        total_qty: b.total_qty,
        warehouses: Array.isArray(b.warehouses) ? b.warehouses : [],
      }));
    }
    // حالت واقعی: گروه‌بندی بر اساس product (int ID)
    const map = new Map<number, GroupedRow>();
    for (const b of rawRows as any[]) {
      const pid = Number(b.product ?? b.product_id);
      if (!pid) continue;
      if (!map.has(pid)) {
        map.set(pid, {
          product_id: pid,
          product_name: b.product_name ?? b.product?.name ?? "—",
          product_code: b.product_code ?? b.product?.code ?? "—",
          total_qty: "0",
          warehouses: [],
        });
      }
      const entry = map.get(pid)!;
      const qty = parseFloat(b.qty_on_hand ?? b.qty ?? "0") || 0;
      const totalQty = parseFloat(entry.total_qty) || 0;
      entry.total_qty = String(totalQty + qty);
      entry.warehouses.push({
        warehouse_id: Number(b.warehouse_id ?? b.warehouse?.id ?? 0),
        warehouse_name: b.warehouse_name ?? b.warehouse?.name ?? "—",
        qty: b.qty_on_hand ?? b.qty ?? "0",
      });
    }
    return Array.from(map.values());
  }, [rawRows, isMocked]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><Boxes className="h-5 w-5" /> موجودی تجمیعی</CardTitle>
        <CardDescription>موجودی هر محصول به تفکیک انبار</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">محصول</TableHead>
                <TableHead className="text-right">کد</TableHead>
                <TableHead className="text-right">موجودی کل</TableHead>
                <TableHead className="text-right">تفکیک انبارها</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={4} className="p-0"><TableSkeleton rows={8} cols={4} /></TableCell></TableRow>
              ) : rows.length === 0 ? (
                <TableRow><TableCell colSpan={4}><EmptyState /></TableCell></TableRow>
              ) : (
                rows.map((b) => (
                  <TableRow key={b.product_id}>
                    <TableCell className="font-medium">{b.product_name}</TableCell>
                    <TableCell className="font-mono nums" dir="ltr">{b.product_code}</TableCell>
                    <TableCell className="nums font-semibold" dir="ltr">{formatNumber(b.total_qty)}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {b.warehouses.length === 0 ? (
                          <span>—</span>
                        ) : (
                          b.warehouses.map((w, i) => (
                            <Badge key={`${w.warehouse_id}-${i}`} variant="secondary" className="nums">
                              {w.warehouse_name}: {formatNumber(w.qty)}
                            </Badge>
                          ))
                        )}
                      </div>
                    </TableCell>
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

function LotsTab({ onAllocate }: { onAllocate: () => void }) {
  const [filter, setFilter] = React.useState<"all" | "near_expiry">("all");
  const [page, setPage] = React.useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["lots", { filter, page, page_size: pageSize }],
    queryFn: () =>
      filter === "near_expiry"
        ? api<Paginated<Lot>>("/inventory/lots/near_expiry/", { query: { days: 20, page, page_size: pageSize } })
        : api<Paginated<Lot>>("/inventory/lots/", { query: { page, page_size: pageSize } }),
  });

  React.useEffect(() => setPage(1), [filter]);

  const lots = data?.results ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><Layers className="h-5 w-5" /> لیست لات‌ها</CardTitle>
          <CardDescription>لات‌ها با تاریخ انقضا و روزهای باقیمانده</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={(v) => setFilter(v as "all" | "near_expiry")}>
            <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">همه لات‌ها</SelectItem>
              <SelectItem value="near_expiry">نزدیک انقضا</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={onAllocate}>
            <Wand2 className="h-4 w-4" />
            تخصیص FEFO
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="flex items-center gap-2 px-4 py-2 text-xs">
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> ≤ ۳ روز</span>
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> ≤ ۷ روز</span>
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-yellow-500" /> ≤ ۱۴ روز</span>
          <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> بیشتر</span>
        </div>
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">لات</TableHead>
                <TableHead className="text-right">محصول</TableHead>
                <TableHead className="text-right">انبار</TableHead>
                <TableHead className="text-right">موجودی</TableHead>
                <TableHead className="text-right">تاریخ انقضا</TableHead>
                <TableHead className="text-right">روزهای باقیمانده</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="p-0"><TableSkeleton rows={8} cols={6} /></TableCell></TableRow>
              ) : lots.length === 0 ? (
                <TableRow><TableCell colSpan={6}><EmptyState /></TableCell></TableRow>
              ) : (
                lots.map((l) => {
                  const tone = expiryTone(l.expiry_date);
                  return (
                    <TableRow key={l.id}>
                      <TableCell className="font-mono nums" dir="ltr">{l.lot_no}</TableCell>
                      <TableCell className="font-medium">{l.product?.name}</TableCell>
                      <TableCell>{l.warehouse?.name}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatNumber(l.qty_on_hand)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(l.expiry_date)}</TableCell>
                      <TableCell className={tone.cls}>
                        <span className="inline-flex items-center gap-1">
                          {tone.label === "منقضی" && <AlertTriangle className="h-3.5 w-3.5" />}
                          <span className="nums">{tone.label}</span>
                        </span>
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
    </Card>
  );
}

export function InventoryView() {
  const [allocateOpen, setAllocateOpen] = React.useState(false);
  return (
    <div className="space-y-4">
      <Tabs defaultValue="balance">
        <TabsList>
          <TabsTrigger value="balance">موجودی</TabsTrigger>
          <TabsTrigger value="lots">لات‌ها (FEFO)</TabsTrigger>
        </TabsList>
        <TabsContent value="balance" className="mt-4">
          <StockBalanceTab />
        </TabsContent>
        <TabsContent value="lots" className="mt-4">
          <LotsTab onAllocate={() => setAllocateOpen(true)} />
        </TabsContent>
      </Tabs>
      <AllocateFefoDialog open={allocateOpen} onOpenChange={setAllocateOpen} />
    </div>
  );
}
