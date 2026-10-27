"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Plus, Trash2, Eye, MoreHorizontal, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_SALES, MOCK_PRODUCTS, MOCK_STORES } from "@/lib/mock-data";
import { formatRial, formatNumber, formatDateTime } from "@/lib/format";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pager, SearchInput, TableSkeleton, EmptyState, useDebounced } from "@/components/common";

type Sale = (typeof MOCK_SALES)[number];
type Product = (typeof MOCK_PRODUCTS)[number];
type Store = (typeof MOCK_STORES)[number];

// Helpers برای استخراج نام فروشگاه و محصول — backend این مقادیر رو
// به‌صورت store_name و product_name برمی‌گردونه، نه به‌صورت object.
function saleStoreName(s: Sale | undefined | null): string {
  if (!s) return "—";
  const sn = (s as any).store_name;
  return sn ?? (s as any).store?.name ?? `فروشگاه ${(s as any).store_id ?? "?"}`;
}
function saleProductName(l: { product_name?: string; product_code?: string; [key: string]: unknown }): string {
  return l.product_name ?? l.product_code ?? "—";
}

const SALES_TYPE_LABEL: Record<string, string> = {
  consignment: "امانی",
  firm: "قطعی",
};

const SALES_STATUS_LABEL: Record<string, string> = {
  draft: "پیش‌نویس",
  pending: "در انتظار",
  reviewing: "در حال بررسی",
  approved: "تأییدشده",
  rejected: "رد‌شده",
  confirmed: "تأییدشده",
  delivered: "تحویل‌شده",
  invoiced: "فاکتورشده",
  posted: "ثبت‌شده",
  returned: "برگشتی",
  canceled: "لغوشده",
};

interface LineInput {
  product_id: string;
  qty: string;
  unit_price: string;
}

function CreateSaleDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [storeId, setStoreId] = React.useState("");
  const [salesType, setSalesType] = React.useState("consignment");
  const [lines, setLines] = React.useState<LineInput[]>([{ product_id: "", qty: "1", unit_price: "30000" }]);

  const { data: stores } = useQuery({
    queryKey: ["stores-options"],
    queryFn: () => api<Paginated<Store>>("/partners/stores/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });
  const { data: products } = useQuery({
    queryKey: ["products-options-sales"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const total = lines.reduce((s, l) => s + (parseFloat(l.qty) || 0) * (parseFloat(l.unit_price) || 0), 0);

  const addLine = () => setLines((l) => [...l, { product_id: "", qty: "1", unit_price: "30000" }]);
  const removeLine = (i: number) => setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<LineInput>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const mutation = useMutation({
    mutationFn: () =>
      api("/sales/create_sale/", {
        method: "POST",
        body: {
          store_id: Number(storeId),
          sales_type: salesType,
          lines: lines.map((l) => ({
            product_id: Number(l.product_id),
            qty: l.qty,
            unit_price: l.unit_price,
          })),
        },
      }),
    onSuccess: () => {
      toast.success("فروش جدید ثبت شد.");
      qc.invalidateQueries({ queryKey: ["sales"] });
      setStoreId("");
      setSalesType("consignment");
      setLines([{ product_id: "", qty: "1", unit_price: "30000" }]);
      onOpenChange(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>فروش جدید</DialogTitle>
          <DialogDescription>فاکتور فروش با چندین خط ایجاد کنید.</DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
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
            <Label>نوع فروش</Label>
            <Select value={salesType} onValueChange={setSalesType}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="consignment">امانی</SelectItem>
                <SelectItem value="cash">نقدی</SelectItem>
                <SelectItem value="credit">اعتباری</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="rounded-lg border">
          <div className="grid grid-cols-[1fr_90px_120px_40px] gap-2 border-b bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
            <span>محصول</span>
            <span className="text-right">تعداد</span>
            <span className="text-right">قیمت واحد</span>
            <span />
          </div>
          <div className="max-h-64 overflow-y-auto scroll-pretty">
            {lines.map((l, i) => (
              <div key={i} className="grid grid-cols-[1fr_90px_120px_40px] gap-2 border-b last:border-0 px-3 py-2">
                <Select value={l.product_id} onValueChange={(v) => updateLine(i, { product_id: v })}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                  <SelectContent>
                    {products?.results.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input className="h-9 nums" dir="ltr" value={l.qty} onChange={(e) => updateLine(i, { qty: e.target.value })} type="number" />
                <Input className="h-9 nums" dir="ltr" value={l.unit_price} onChange={(e) => updateLine(i, { unit_price: e.target.value })} type="number" />
                <Button variant="ghost" size="icon" onClick={() => removeLine(i)} disabled={lines.length === 1} aria-label="حذف خط">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between px-3 py-2">
            <Button variant="outline" size="sm" onClick={addLine}>
              <Plus className="h-4 w-4" /> افزودن خط
            </Button>
            <span className="text-sm font-medium nums">جمع کل: {formatRial(total)}</span>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !storeId || lines.some((l) => !l.product_id)}>
            {mutation.isPending ? "در حال ثبت…" : "ثبت فروش"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SaleDetailsDialog({ sale, onOpenChange }: { sale: Sale | null; onOpenChange: (v: boolean) => void }) {
  const { data: detail, isLoading } = useQuery({
    queryKey: ["sale-detail", sale?.id],
    queryFn: () => api<Sale & { lines?: any[] }>(`/sales/${sale!.id}/`),
    enabled: sale !== null,
  });
  const lines = detail?.lines ?? (sale?.lines ?? []);
  return (
    <Dialog open={sale !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>جزئیات فروش {sale?.sale_no}</DialogTitle>
          <DialogDescription>{saleStoreName(sale)} — {SALES_TYPE_LABEL[sale?.sales_type ?? ""]}</DialogDescription>
        </DialogHeader>
        {sale && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><p className="text-xs text-muted-foreground">مبلغ کل</p><p className="font-semibold nums">{formatRial(sale.total_amount)}</p></div>
              <div><p className="text-xs text-muted-foreground">بهای تمام‌شده</p><p className="font-semibold nums">{formatRial(sale.total_cost)}</p></div>
              <div><p className="text-xs text-muted-foreground">سود</p><p className="font-semibold text-emerald-600 dark:text-emerald-400 nums">{formatRial(sale.total_profit)}</p></div>
            </div>
            <div className="rounded-lg border overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">تعداد</TableHead>
                    <TableHead className="text-right">قیمت واحد</TableHead>
                    <TableHead className="text-right">جمع خط</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-4">در حال بارگذاری خطوط…</TableCell></TableRow>
                  ) : lines.length === 0 ? (
                    <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-4">خطوطی یافت نشد.</TableCell></TableRow>
                  ) : (
                    lines.map((l: any, i: number) => (
                      <TableRow key={l.id ?? i}>
                        <TableCell className="font-medium">{saleProductName(l)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(l.qty)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(l.unit_price)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(l.line_total)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ====================================================================
// برگشت از فروش
// ====================================================================

interface ReturnLineInput {
  product_id: string;
  qty: string;
  condition: string;
}

const RETURN_CONDITION_LABEL: Record<string, string> = {
  sellable: "قابل فروش مجدد",
  expired: "منقضی",
  damaged: "آسیب‌دیده",
  near_expiry: "نزدیک به انقضا",
};

function CreateReturnDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [storeId, setStoreId] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [returnDate, setReturnDate] = React.useState(new Date().toISOString().slice(0, 10));
  const [lines, setLines] = React.useState<ReturnLineInput[]>([{ product_id: "", qty: "1", condition: "sellable" }]);

  const { data: stores } = useQuery({
    queryKey: ["stores-options-return"],
    queryFn: () => api<Paginated<Store>>("/partners/stores/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });
  const { data: products } = useQuery({
    queryKey: ["products-options-return"],
    queryFn: () => api<Paginated<Product>>("/products/", { query: { page: 1, page_size: 100 } }),
    enabled: open,
  });

  const addLine = () => setLines((l) => [...l, { product_id: "", qty: "1", condition: "sellable" }]);
  const removeLine = (i: number) => setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<ReturnLineInput>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const mutation = useMutation({
    mutationFn: () =>
      api("/sales/returns/create/", {
        method: "POST",
        body: {
          store_id: Number(storeId),
          return_date: returnDate,
          reason,
          lines: lines.map((l) => ({
            product_id: Number(l.product_id),
            qty: l.qty,
            condition: l.condition,
          })),
        },
      }),
    onSuccess: () => {
      toast.success("برگشت از فروش ثبت شد.");
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["returns"] });
      setStoreId("");
      setReason("");
      setLines([{ product_id: "", qty: "1", condition: "sellable" }]);
      onOpenChange(false);
    },
    onError: (e: Error) => {
      let msg = e instanceof Error ? e.message : "خطا در ثبت برگشت.";
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
          <DialogTitle>برگشت از فروش</DialogTitle>
          <DialogDescription>ثبت کالای برگشتی از فروشگاه با تعیین وضعیت</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>فروشگاه</Label>
              <Select value={storeId} onValueChange={setStoreId}>
                <SelectTrigger><SelectValue placeholder="انتخاب فروشگاه" /></SelectTrigger>
                <SelectContent>
                  {stores?.results.map((s) => (
                    <SelectItem key={s.id} value={String(s.id)}>{s.name} — {s.code}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>تاریخ برگشت</Label>
              <Input type="date" dir="ltr" className="nums" value={returnDate} onChange={(e) => setReturnDate(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>علت برگشت (اختیاری)</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="مثلاً: انقضای کالا" />
          </div>

          <div className="rounded-lg border">
            <div className="grid grid-cols-[1fr_90px_140px_40px] gap-2 border-b bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
              <span>محصول</span>
              <span className="text-right">تعداد</span>
              <span className="text-right">وضعیت</span>
              <span />
            </div>
            <div className="max-h-64 overflow-y-auto scroll-pretty">
              {lines.map((l, i) => (
                <div key={i} className="grid grid-cols-[1fr_90px_140px_40px] gap-2 border-b last:border-0 px-3 py-2">
                  <Select value={l.product_id} onValueChange={(v) => updateLine(i, { product_id: v })}>
                    <SelectTrigger className="h-9"><SelectValue placeholder="انتخاب محصول" /></SelectTrigger>
                    <SelectContent>
                      {products?.results.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>{p.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input className="h-9 nums" dir="ltr" value={l.qty} onChange={(e) => updateLine(i, { qty: e.target.value })} type="number" min="1" />
                  <Select value={l.condition} onValueChange={(v) => updateLine(i, { condition: v })}>
                    <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {Object.entries(RETURN_CONDITION_LABEL).map(([v, label]) => (
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
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !storeId || lines.some((l) => !l.product_id)}>
            {mutation.isPending ? "در حال ثبت…" : "ثبت برگشت"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function SalesView() {
  const [search, setSearch] = React.useState("");
  const debounced = useDebounced(search);
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [createOpen, setCreateOpen] = React.useState(false);
  const [returnOpen, setReturnOpen] = React.useState(false);
  const [viewing, setViewing] = React.useState<Sale | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["sales", { page, page_size: pageSize, search: debounced }],
    queryFn: () =>
      api<Paginated<Sale>>("/sales/", {
        query: { page, page_size: pageSize, search: debounced || undefined },
      }),
  });

  React.useEffect(() => setPage(1), [debounced]);

  const sales = data?.results ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>مدیریت فروش</CardTitle>
            <CardDescription>فاکتورهای فروش همراه با مبلغ، بهای تمام‌شده و سود</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setReturnOpen(true)}>
              <RotateCcw className="h-4 w-4" />
              برگشت از فروش
            </Button>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              فروش جدید
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="p-4">
            <SearchInput value={search} onChange={setSearch} placeholder="جستجو بر اساس شماره یا فروشگاه…" className="sm:max-w-xs" />
          </div>

          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">شماره</TableHead>
                  <TableHead className="text-right">فروشگاه</TableHead>
                  <TableHead className="text-right">نوع</TableHead>
                  <TableHead className="text-right">وضعیت</TableHead>
                  <TableHead className="text-right">مبلغ کل</TableHead>
                  <TableHead className="text-right">بهای تمام‌شده</TableHead>
                  <TableHead className="text-right">سود</TableHead>
                  <TableHead className="text-right">تاریخ</TableHead>
                  <TableHead className="text-right w-16">عملیات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={9} className="p-0"><TableSkeleton rows={8} cols={9} /></TableCell>
                  </TableRow>
                ) : sales.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9}><EmptyState description="فروشی یافت نشد." /></TableCell>
                  </TableRow>
                ) : (
                  sales.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell className="font-mono nums" dir="ltr">{s.sale_no}</TableCell>
                      <TableCell className="font-medium">{saleStoreName(s)}</TableCell>
                      <TableCell><Badge variant="outline">{SALES_TYPE_LABEL[s.sales_type] ?? s.sales_type}</Badge></TableCell>
                      <TableCell><Badge variant="secondary">{SALES_STATUS_LABEL[s.status] ?? s.status}</Badge></TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(s.total_amount)}</TableCell>
                      <TableCell className="nums text-muted-foreground" dir="ltr">{formatRial(s.total_cost)}</TableCell>
                      <TableCell className="nums font-medium text-emerald-600 dark:text-emerald-400" dir="ltr">{formatRial(s.total_profit)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground" dir="ltr">{formatDateTime(s.created_at)}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label="عملیات"><MoreHorizontal className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => setViewing(s)}>
                              <Eye className="h-4 w-4" />
                              مشاهده جزئیات
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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

      <CreateSaleDialog open={createOpen} onOpenChange={setCreateOpen} />
      <CreateReturnDialog open={returnOpen} onOpenChange={setReturnOpen} />
      <SaleDetailsDialog sale={viewing} onOpenChange={(v) => !v && setViewing(null)} />
    </div>
  );
}
