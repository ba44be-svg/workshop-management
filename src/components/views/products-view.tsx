"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { MoreHorizontal, Pencil, Plus, Trash2, Eye } from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_PRODUCTS } from "@/lib/mock-data";
import { formatNumber } from "@/lib/format";
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
import {
  Pager,
  SearchInput,
  TableSkeleton,
  EmptyState,
  ConfirmDialog,
  useDebounced,
} from "@/components/common";

// -----------------------------------------------------------------------------
// Types — با backend واقعی Django هم‌خوان است (snake_case)
// -----------------------------------------------------------------------------
interface ProductCategory {
  id: number;
  code: string;
  name: string;
  parent: number | null;
  level: number;
  is_active: boolean;
  products_count?: number;
}

interface Unit {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

interface Product {
  id: number;
  code: string;
  name: string;
  category: number; // FK ID
  category_name?: string;
  unit: number; // FK ID (Unit)
  unit_code?: string;
  unit_name?: string;
  is_finished_good?: boolean;
  shelf_life_days: number;
  default_price: string; // decimal as string (e.g. "50000.0000")
  barcode: string | null;
  is_active: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

const FALLBACK_UNIT_OPTIONS: Unit[] = [
  { id: 1, code: "NUM",  name: "عدد",    is_active: true },
  { id: 2, code: "KG",   name: "کیلوگرم", is_active: true },
  { id: 3, code: "G",    name: "گرم",     is_active: true },
  { id: 4, code: "L",    name: "لیتر",    is_active: true },
  { id: 5, code: "PACK", name: "بسته",   is_active: true },
];

// -----------------------------------------------------------------------------
// Helper: ساخت payload صحیح برای ارسال به backend
// -----------------------------------------------------------------------------
function buildPayload(form: FormState): Record<string, unknown> {
  return {
    code: form.code.trim(),
    name: form.name.trim(),
    category: Number(form.category), // FK ID
    unit: Number(form.unit), // FK ID (Unit)
    is_finished_good: form.is_finished_good,
    shelf_life_days: Number(form.shelf_life_days),
    default_price: Number(form.default_price).toFixed(4), // "50000.0000"
    barcode: form.barcode.trim() || null, // backend خودش EAN-13 می‌سازد اگر null بفرستیم
    is_active: form.is_active,
    description: form.description?.trim() ?? "",
  };
}

// -----------------------------------------------------------------------------
// Form
// -----------------------------------------------------------------------------
interface FormState {
  code: string;
  name: string;
  barcode: string;
  default_price: string;
  unit: string; // FK ID as string (for Select value)
  is_finished_good: boolean;
  category: string; // FK ID as string (for Select value)
  shelf_life_days: string;
  is_active: boolean;
  description: string;
}

const EMPTY_FORM: FormState = {
  code: "",
  name: "",
  barcode: "",
  default_price: "0",
  unit: "1",
  is_finished_good: false,
  category: "",
  shelf_life_days: "3",
  is_active: true,
  description: "",
};

function ProductFormDialog({
  open,
  onOpenChange,
  product,
  categories,
  units,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  product: Product | null;
  categories: ProductCategory[];
  units: Unit[];
  onSaved: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = React.useState<FormState>(EMPTY_FORM);
  const isEdit = product !== null;

  React.useEffect(() => {
    if (!open) return;
    if (product) {
      setForm({
        code: product.code,
        name: product.name,
        barcode: product.barcode ?? "",
        default_price: String(parseFloat(product.default_price) || 0),
        unit: String(product.unit ?? 1),
        is_finished_good: product.is_finished_good ?? false,
        category: String(product.category),
        shelf_life_days: String(product.shelf_life_days),
        is_active: product.is_active,
        description: product.description ?? "",
      });
    } else {
      // پیش‌انتخاب اولین دسته‌بندی به‌عنوان پیش‌فرض
      setForm({
        ...EMPTY_FORM,
        category: categories[0] ? String(categories[0].id) : "",
        unit: units[0] ? String(units[0].id) : "1",
      });
    }
  }, [open, product, categories, units]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = buildPayload(form);
      if (isEdit) {
        return api<Product>(`/products/${product!.id}/`, {
          method: "PUT",
          body: payload,
        });
      }
      return api<Product>("/products/", {
        method: "POST",
        body: payload,
      });
    },
    onSuccess: () => {
      toast.success(isEdit ? "محصول ویرایش شد." : "محصول با موفقیت ساخته شد.");
      qc.invalidateQueries({ queryKey: ["products"] });
      onOpenChange(false);
      onSaved();
    },
    onError: (e: Error) => {
      const msg = e instanceof Error ? e.message : "خطا در ثبت محصول";
      toast.error(msg);
    },
  });

  const set = <K extends keyof FormState>(k: K, v: FormState[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "ویرایش محصول" : "محصول جدید"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "اطلاعات محصول را به‌روز کنید."
              : "فرم زیر را برای ساخت محصول جدید تکمیل کنید."}
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="p-code">کد محصول</Label>
            <Input
              id="p-code"
              value={form.code}
              onChange={(e) => set("code", e.target.value)}
              placeholder="P001"
              dir="ltr"
              className="nums"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-name">نام</Label>
            <Input
              id="p-name"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="نان بربری"
            />
          </div>
          <div className="space-y-1.5 col-span-2">
            <Label htmlFor="p-barcode">بارکد EAN-13 (اختیاری — خالی بگذارید تا خودکار ساخته شود)</Label>
            <Input
              id="p-barcode"
              value={form.barcode}
              onChange={(e) => set("barcode", e.target.value)}
              dir="ltr"
              className="nums"
              placeholder="خالی = تولید خودکار با پیشوند ۶۴۲"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-price">قیمت پایه (ریال)</Label>
            <Input
              id="p-price"
              value={form.default_price}
              onChange={(e) => set("default_price", e.target.value)}
              dir="ltr"
              className="nums"
              type="number"
              min="0"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-unit">واحد</Label>
            <Select value={form.unit} onValueChange={(v) => set("unit", v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {units.map((u) => (
                  <SelectItem key={u.id} value={String(u.id)}>
                    {u.name} — {u.code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-fg">نوع محصول</Label>
            <Select
              value={form.is_finished_good ? "finished" : "raw"}
              onValueChange={(v) => set("is_finished_good", v === "finished")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="raw">ماده اولیه</SelectItem>
                <SelectItem value="finished">محصول تمام‌شده</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-cat">دسته‌بندی</Label>
            <Select
              value={form.category}
              onValueChange={(v) => set("category", v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="انتخاب دسته…" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.code} — {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p-shelf">عمرفنی (روز)</Label>
            <Input
              id="p-shelf"
              type="number"
              min="1"
              value={form.shelf_life_days}
              onChange={(e) => set("shelf_life_days", e.target.value)}
              dir="ltr"
              className="nums"
            />
          </div>
          <div className="space-y-1.5 col-span-2">
            <Label>وضعیت</Label>
            <Select
              value={form.is_active ? "active" : "inactive"}
              onValueChange={(v) => set("is_active", v === "active")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">فعال</SelectItem>
                <SelectItem value="inactive">غیرفعال</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5 col-span-2">
            <Label htmlFor="p-desc">توضیحات</Label>
            <Input
              id="p-desc"
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              placeholder="توضیحات اختیاری…"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            انصراف
          </Button>
          <Button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending
              ? "در حال ذخیره…"
              : isEdit
              ? "ذخیره تغییرات"
              : "ساخت محصول"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ProductDetailsDialog({
  product,
  onOpenChange,
}: {
  product: Product | null;
  onOpenChange: (v: boolean) => void;
}) {
  return (
    <Dialog open={product !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>جزئیات محصول</DialogTitle>
          <DialogDescription>{product?.name}</DialogDescription>
        </DialogHeader>
        {product && (
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Detail label="کد" value={product.code} mono />
            <Detail label="بارکد" value={product.barcode ?? "—"} mono />
            <Detail
              label="قیمت پایه"
              value={`${formatNumber(product.default_price)} ریال`}
            />
            <Detail label="واحد" value={product.unit_name ?? `#${product.unit}`} />
            <Detail label="دسته" value={product.category_name ?? `#${product.category}`} />
            <Detail label="عمرفنی" value={`${product.shelf_life_days} روز`} />
            <div className="col-span-2 flex items-center gap-2">
              <span className="text-muted-foreground">نوع محصول:</span>
              <Badge variant={product.is_finished_good ? "default" : "secondary"}>
                {product.is_finished_good ? "محصول تمام‌شده" : "ماده اولیه"}
              </Badge>
            </div>
            <div className="col-span-2 flex items-center gap-2">
              <span className="text-muted-foreground">وضعیت:</span>
              <Badge variant={product.is_active ? "default" : "secondary"}>
                {product.is_active ? "فعال" : "غیرفعال"}
              </Badge>
            </div>
            {product.description && (
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground mb-1">توضیحات</p>
                <p className="font-medium">{product.description}</p>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Detail({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="space-y-0.5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p
        className={`font-medium ${mono ? "font-mono nums" : ""}`}
        dir={mono ? "ltr" : undefined}
      >
        {value}
      </p>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Main view
// -----------------------------------------------------------------------------
export function ProductsView() {
  const [search, setSearch] = React.useState("");
  const debounced = useDebounced(search);
  const [statusFilter, setStatusFilter] = React.useState<string>("all"); // all | active | inactive | finished | raw
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Product | null>(null);
  const [viewing, setViewing] = React.useState<Product | null>(null);
  const [deleting, setDeleting] = React.useState<Product | null>(null);
  const qc = useQueryClient();

  // 1) بارگذاری دسته‌بندی‌ها از backend
  const { data: categoriesData } = useQuery({
    queryKey: ["product-categories"],
    queryFn: () =>
      api<Paginated<ProductCategory> | ProductCategory[]>(
        "/products/categories/?page_size=200"
      ),
  });
  const categories: ProductCategory[] = React.useMemo(() => {
    if (!categoriesData) return [];
    if (Array.isArray(categoriesData)) return categoriesData;
    return categoriesData.results ?? [];
  }, [categoriesData]);

  // 1.5) بارگذاری واحدها از backend
  const { data: unitsData } = useQuery({
    queryKey: ["product-units"],
    queryFn: () =>
      api<Paginated<Unit> | Unit[]>(
        "/products/units/?page_size=200"
      ),
  });
  const units: Unit[] = React.useMemo(() => {
    if (!unitsData) return FALLBACK_UNIT_OPTIONS;
    if (Array.isArray(unitsData)) return unitsData;
    return unitsData.results ?? FALLBACK_UNIT_OPTIONS;
  }, [unitsData]);

  // 2) لیست محصولات
  const { data, isLoading } = useQuery({
    queryKey: ["products", { page, page_size: pageSize, search: debounced, status: statusFilter }],
    queryFn: () =>
      api<Paginated<Product>>("/products/", {
        query: {
          page,
          page_size: pageSize,
          search: debounced || undefined,
          is_active:
            statusFilter === "all" || statusFilter === "finished" || statusFilter === "raw"
              ? undefined
              : statusFilter === "active",
        },
      }),
  });

  React.useEffect(() => {
    setPage(1);
  }, [debounced, statusFilter]);

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api(`/products/${id}/`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success("محصول حذف شد.");
      setDeleting(null);
      qc.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const allProducts = data?.results ?? [];
  const products =
    statusFilter === "finished"
      ? allProducts.filter((p) => p.is_finished_good)
      : statusFilter === "raw"
      ? allProducts.filter((p) => !p.is_finished_good)
      : allProducts;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>محصولات</CardTitle>
            <CardDescription>
              لیست کامل محصولات — مواد اولیه و محصولات تمام‌شده
            </CardDescription>
          </div>
          <Button
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            <Plus className="h-4 w-4" />
            محصول جدید
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="جستجو بر اساس کد، نام یا بارکد…"
              className="sm:max-w-xs"
            />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="sm:w-44">
                <SelectValue placeholder="همه نوع‌ها" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">همه</SelectItem>
                <SelectItem value="active">فعال</SelectItem>
                <SelectItem value="inactive">غیرفعال</SelectItem>
                <SelectItem value="finished">محصول تمام‌شده</SelectItem>
                <SelectItem value="raw">ماده اولیه</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">کد</TableHead>
                  <TableHead className="text-right">نام محصول</TableHead>
                  <TableHead className="text-right">بارکد EAN-13</TableHead>
                  <TableHead className="text-right">قیمت پایه</TableHead>
                  <TableHead className="text-right">دسته</TableHead>
                  <TableHead className="text-right">نوع</TableHead>
                  <TableHead className="text-right">وضعیت</TableHead>
                  <TableHead className="text-right w-16">عملیات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="p-0">
                      <TableSkeleton rows={8} cols={8} />
                    </TableCell>
                  </TableRow>
                ) : products.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8}>
                      <EmptyState description="محصولی با این فیلترها یافت نشد." />
                    </TableCell>
                  </TableRow>
                ) : (
                  products.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-mono nums" dir="ltr">
                        {p.code}
                      </TableCell>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell className="font-mono nums" dir="ltr">
                        {p.barcode ?? "—"}
                      </TableCell>
                      <TableCell className="nums" dir="ltr">
                        {formatNumber(p.default_price)}
                      </TableCell>
                      <TableCell>{p.category_name ?? `#${p.category}`}</TableCell>
                      <TableCell>
                        <Badge variant={p.is_finished_good ? "default" : "secondary"}>
                          {p.is_finished_good ? "محصول" : "ماده اولیه"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={p.is_active ? "default" : "secondary"}>
                          {p.is_active ? "فعال" : "غیرفعال"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label="عملیات"
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => setViewing(p)}>
                              <Eye className="h-4 w-4" />
                              جزئیات
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => {
                                setEditing(p);
                                setFormOpen(true);
                              }}
                            >
                              <Pencil className="h-4 w-4" />
                              ویرایش
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() => setDeleting(p)}
                            >
                              <Trash2 className="h-4 w-4" />
                              حذف
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

          <Pager
            page={page}
            pageSize={pageSize}
            count={data?.count ?? 0}
            onPage={setPage}
          />
        </CardContent>
      </Card>

      <ProductFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        product={editing}
        categories={categories}
        units={units}
        onSaved={() => {}}
      />
      <ProductDetailsDialog
        product={viewing}
        onOpenChange={(v) => !v && setViewing(null)}
      />
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(v) => !v && setDeleting(null)}
        title="حذف محصول"
        description={`آیا از حذف «${deleting?.name}» مطمئن هستید؟ این عمل قابل بازگشت نیست.`}
        confirmText="حذف"
        tone="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </div>
  );
}

// برا اینکه TypeScript از "اشاره به MOCK_PRODUCTS استفاده نشده" گله نکند:
// (در نسخه‌ی قبلی برای استنتاج type استفاده می‌شد؛ حالا type صریح داریم.)
void MOCK_PRODUCTS;
