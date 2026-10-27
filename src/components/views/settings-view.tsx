"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import {
  Boxes,
  Building2,
  CheckCircle2,
  Factory,
  Package,
  Plus,
  RefreshCw,
  Save,
  ServerCog,
  Shield,
  User as UserIcon,
  XCircle,
} from "lucide-react";
import { api, isDemoMode, resetBackendProbe, type Paginated } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { useConfig, ICON_MAP, type IconKey, type Theme, type Layout } from "@/store/config-store";
import { THEME_LIST } from "@/lib/themes";
import { setCalendarMode as persistCalendarMode, todayISO, type CalendarMode } from "@/lib/calendar";
import { MOCK_USERS, MOCK_COMPANY, MOCK_ROLES } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ConfirmDialog } from "@/components/common";
import { DatePicker } from "@/components/dialogs/datepicker";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type User = (typeof MOCK_USERS)[number];
type Company = typeof MOCK_COMPANY;
type Role = (typeof MOCK_ROLES)[number];

const ROLE_LABEL: Record<string, string> = {
  admin: "مدیر سیستم",
  accountant: "حسابدار",
  storekeeper: "انباردار",
  distributor: "عامل پخش",
  sales: "فروشنده",
  viewer: "بیننده",
};

const PERMISSION_LABEL: Record<string, string> = {
  dashboard: "داشبورد",
  products: "محصولات",
  production: "تولید",
  sales: "فروش",
  inventory: "انبار",
  accounting: "حسابداری",
  dispatch: "پخش",
  reports: "گزارش‌ها",
  settings: "تنظیمات",
};

const ALL_PERMISSIONS = ["dashboard", "products", "production", "sales", "inventory", "accounting", "dispatch", "reports", "settings"];

// ---------------------------------------------------------------------------
// 1) Profile tab
// ---------------------------------------------------------------------------

function ProfileTab() {
  const { user } = useAuthStore();
  const [firstName, setFirstName] = React.useState(user?.first_name ?? "");
  const [lastName, setLastName] = React.useState(user?.last_name ?? "");
  const [email, setEmail] = React.useState(user?.email ?? "");
  const [oldPassword, setOldPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [savingProfile, setSavingProfile] = React.useState(false);
  const [savingPassword, setSavingPassword] = React.useState(false);

  const initials = `${firstName?.[0] ?? ""}${lastName?.[0] ?? ""}`;

  const onProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await api("/auth/me/", { method: "PATCH", body: { first_name: firstName, last_name: lastName, email } });
      toast.success("پروفایل به‌روزرسانی شد.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "خطا در به‌روزرسانی پروفایل.");
    } finally {
      setSavingProfile(false);
    }
  };

  const onPasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oldPassword || !newPassword) {
      toast.error("گذرواژه قدیمی و جدید را وارد کنید.");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("گذرواژه جدید باید حداقل ۸ کاراکتر باشد.");
      return;
    }
    setSavingPassword(true);
    try {
      await api("/auth/change_password/", {
        method: "POST",
        body: { old_password: oldPassword, new_password: newPassword },
      });
      toast.success("گذرواژه با موفقیت تغییر کرد.");
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "خطا در تغییر گذرواژه.");
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><UserIcon className="h-5 w-5" /> اطلاعات کاربری</CardTitle>
          <CardDescription>نام، نام خانوادگی و ایمیل خود را به‌روز کنید</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 pb-4">
            <Avatar className="h-14 w-14">
              <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                {initials || "مک"}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-semibold">{firstName} {lastName}</p>
              <p className="text-xs text-muted-foreground">@{user?.username}</p>
              <Badge variant="secondary" className="mt-1">{ROLE_LABEL[user?.role ?? ""] ?? user?.role ?? "—"}</Badge>
            </div>
          </div>
          <Separator className="my-4" />
          <form onSubmit={onProfileSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="p-first">نام</Label>
                <Input id="p-first" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="p-last">نام خانوادگی</Label>
                <Input id="p-last" value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-email">ایمیل</Label>
              <Input id="p-email" type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <Button type="submit" disabled={savingProfile} className="w-full">
              {savingProfile ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              ذخیره تغییرات
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Shield className="h-5 w-5" /> تغییر گذرواژه</CardTitle>
          <CardDescription>گذرواژه فعلی و گذرواژه جدید را وارد کنید</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onPasswordSubmit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="p-old">گذرواژه فعلی</Label>
              <Input id="p-old" type="password" dir="ltr" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-new">گذرواژه جدید</Label>
              <Input id="p-new" type="password" dir="ltr" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              <p className="text-xs text-muted-foreground">حداقل ۸ کاراکتر شامل حروف و عدد</p>
            </div>
            <Button type="submit" disabled={savingPassword} className="w-full">
              {savingPassword ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
              تغییر گذرواژه
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2) Users tab
// ---------------------------------------------------------------------------

function CreateUserDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [username, setUsername] = React.useState("");
  const [firstName, setFirstName] = React.useState("");
  const [lastName, setLastName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [role, setRole] = React.useState("viewer");
  const [password, setPassword] = React.useState("");
  const [isActive, setIsActive] = React.useState(true);

  const mutation = useMutation({
    mutationFn: () =>
      api<User>("/auth/users/", {
        method: "POST",
        body: { username, first_name: firstName, last_name: lastName, email, role, password, is_active: isActive },
      }),
    onSuccess: (next) => {
      toast.success(`کاربر «${next.username}» اضافه شد.`);
      qc.setQueryData<Paginated<User>>(["users-list"], (old) => {
        if (!old) return old;
        return { ...old, results: [next, ...old.results], count: old.count + 1 };
      });
      setUsername(""); setFirstName(""); setLastName(""); setEmail(""); setRole("viewer"); setPassword(""); setIsActive(true);
      onOpenChange(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>افزودن کاربر جدید</DialogTitle>
          <DialogDescription>کاربر جدید با نقش مشخص‌شده ایجاد کنید.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="u-username">نام کاربری</Label>
              <Input id="u-username" dir="ltr" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="u-role">نقش</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(ROLE_LABEL).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="u-first">نام</Label>
              <Input id="u-first" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="u-last">نام خانوادگی</Label>
              <Input id="u-last" value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-email">ایمیل</Label>
            <Input id="u-email" type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-pass">گذرواژه اولیه</Label>
            <Input id="u-pass" type="password" dir="ltr" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">فعال‌سازی حساب</p>
              <p className="text-xs text-muted-foreground">کاربر می‌تواند وارد سیستم شود</p>
            </div>
            <Switch checked={isActive} onCheckedChange={setIsActive} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !username || !password}>
            {mutation.isPending ? "در حال افزودن…" : "افزودن کاربر"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function UsersTab() {
  const [createOpen, setCreateOpen] = React.useState(false);
  const { data, isLoading } = useQuery<Paginated<User>>({
    queryKey: ["users-list"],
    queryFn: () => api<Paginated<User>>("/auth/users/", { query: { page: 1, page_size: 50 } }),
  });
  const users = data?.results ?? [];
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">مدیریت کاربران</CardTitle>
          <CardDescription>کاربران سیستم به همراه نقش و وضعیت</CardDescription>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> افزودن کاربر
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">نام کاربری</TableHead>
                <TableHead className="text-right">نام کامل</TableHead>
                <TableHead className="text-right">نقش</TableHead>
                <TableHead className="text-right">ایمیل</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right w-24">عملیات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">در حال بارگذاری…</TableCell></TableRow>
              ) : users.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">کاربری یافت نشد.</TableCell></TableRow>
              ) : (
                users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-mono nums" dir="ltr">{u.username}</TableCell>
                    <TableCell className="font-medium">{u.first_name} {u.last_name}</TableCell>
                    <TableCell><Badge variant="outline">{ROLE_LABEL[u.role] ?? u.role}</Badge></TableCell>
                    <TableCell className="text-xs text-muted-foreground" dir="ltr">{u.email || "—"}</TableCell>
                    <TableCell>
                      {u.is_active ? (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10">
                          <CheckCircle2 className="h-3 w-3" /> فعال
                        </Badge>
                      ) : (
                        <Badge variant="secondary"><XCircle className="h-3 w-3" /> غیرفعال</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" disabled>ویرایش</Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CreateUserDialog open={createOpen} onOpenChange={setCreateOpen} />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 3) Company tab
// ---------------------------------------------------------------------------

function CompanyTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery<Company>({
    queryKey: ["company"],
    queryFn: () => api<Company>("/auth/company/"),
  });

  const [form, setForm] = React.useState<Partial<Company>>({});
  React.useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const update = (k: keyof Company, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const onSave = async () => {
    try {
      await api("/auth/company/", { method: "PATCH", body: form });
      qc.invalidateQueries({ queryKey: ["company"] });
      toast.success("اطلاعات شرکت ذخیره شد.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "خطا در ذخیره‌سازی.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-base"><Building2 className="h-5 w-5" /> اطلاعات شرکت</CardTitle>
          <CardDescription>نام، مشخصات مالیاتی و آدرس شرکت را مدیریت کنید</CardDescription>
        </div>
        <Button onClick={onSave} disabled={isLoading}>
          <Save className="h-4 w-4" /> ذخیره
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">در حال بارگذاری…</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="c-name">نام تجاری</Label>
              <Input id="c-name" value={form.name ?? ""} onChange={(e) => update("name", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-legal">نام حقوقی</Label>
              <Input id="c-legal" value={form.legal_name ?? ""} onChange={(e) => update("legal_name", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-tax">کد مالیاتی</Label>
              <Input id="c-tax" dir="ltr" className="nums" value={form.tax_id ?? ""} onChange={(e) => update("tax_id", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-econ">کد اقتصادی</Label>
              <Input id="c-econ" dir="ltr" className="nums" value={form.economic_code ?? ""} onChange={(e) => update("economic_code", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-phone">تلفن</Label>
              <Input id="c-phone" dir="ltr" className="nums" value={form.phone ?? ""} onChange={(e) => update("phone", e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="c-city">شهر</Label>
              <Input id="c-city" value={form.city ?? ""} onChange={(e) => update("city", e.target.value)} />
            </div>
            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="c-addr">آدرس</Label>
              <Textarea id="c-addr" rows={3} value={form.address ?? ""} onChange={(e) => update("address", e.target.value)} />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 4) Roles tab
// ---------------------------------------------------------------------------

function RolesTab() {
  const { data: roles } = useQuery<Role[]>({
    queryKey: ["roles-list"],
    queryFn: () => api<Role[]>("/auth/roles/"),
  });
  const { data: usersData } = useQuery<Paginated<User>>({
    queryKey: ["users-list"],
    queryFn: () => api<Paginated<User>>("/auth/users/", { query: { page: 1, page_size: 100 } }),
  });
  const users = usersData?.results ?? [];
  const roleList = roles ?? [];

  const userCountByRole = React.useMemo(() => {
    const map: Record<string, number> = {};
    for (const u of users) map[u.role] = (map[u.role] ?? 0) + 1;
    return map;
  }, [users]);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {roleList.length === 0 ? (
          <Card><CardContent className="text-center text-muted-foreground py-8">نقشی یافت نشد.</CardContent></Card>
        ) : (
          roleList.map((r) => (
            <Card key={r.key}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{r.name}</CardTitle>
                  <Badge variant="secondary" className="nums">{userCountByRole[r.key] ?? 0} کاربر</Badge>
                </div>
                <CardDescription>{r.description}</CardDescription>
              </CardHeader>
            </Card>
          ))
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base"><Shield className="h-5 w-5" /> ماتریس دسترسی‌ها</CardTitle>
          <CardDescription>مقایسه دسترسی نقش‌ها به بخش‌های سیستم</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">بخش</TableHead>
                  {roleList.map((r) => (
                    <TableHead key={r.key} className="text-center">{r.name}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {ALL_PERMISSIONS.map((perm) => (
                  <TableRow key={perm}>
                    <TableCell className="font-medium">{PERMISSION_LABEL[perm]}</TableCell>
                    {roleList.map((r) => {
                      const has = r.permissions.includes(perm);
                      return (
                        <TableCell key={r.key} className="text-center">
                          {has ? (
                            <CheckCircle2 className="inline h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                          ) : (
                            <XCircle className="inline h-4 w-4 text-muted-foreground" />
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 5) System tab
// ---------------------------------------------------------------------------

function ThemeCard() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);
  if (!mounted) return <div className="h-32" />;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">حالت نمایش</CardTitle>
        <CardDescription>تم روشن/تیره/سیستم</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={theme} onValueChange={setTheme} className="grid grid-cols-3 gap-2">
          <label className="flex items-center gap-2 rounded-lg border p-3 cursor-pointer hover:bg-muted/40">
            <RadioGroupItem value="light" />
            <span className="text-sm">روشن</span>
          </label>
          <label className="flex items-center gap-2 rounded-lg border p-3 cursor-pointer hover:bg-muted/40">
            <RadioGroupItem value="dark" />
            <span className="text-sm">تیره</span>
          </label>
          <label className="flex items-center gap-2 rounded-lg border p-3 cursor-pointer hover:bg-muted/40">
            <RadioGroupItem value="system" />
            <span className="text-sm">سیستم</span>
          </label>
        </RadioGroup>
      </CardContent>
    </Card>
  );
}

// Theme picker (Modern / Classic / Corporate) — controls colors, radius, card style.
function AppThemeCard() {
  const { theme, setTheme } = useConfig();
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">تم نمایش</CardTitle>
        <CardDescription>انتخاب پالت رنگی و سبک کارت‌ها</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={theme} onValueChange={(v) => setTheme(v as Theme)} className="grid grid-cols-3 gap-2">
          {THEME_LIST.map(({ key, def }) => (
            <label
              key={key}
              className={`flex flex-col items-center gap-2 rounded-lg border p-3 cursor-pointer hover:bg-muted/40 transition-colors ${
                theme === key ? "border-primary bg-primary/5" : ""
              }`}
            >
              <RadioGroupItem value={key} className="sr-only" />
              <span
                className="h-8 w-8 rounded-full border shadow-sm"
                style={{ background: def.swatch }}
                aria-hidden
              />
              <span className="text-sm font-medium">{def.name}</span>
              <span className="text-[10px] text-muted-foreground text-center leading-tight">{def.description}</span>
            </label>
          ))}
        </RadioGroup>
      </CardContent>
    </Card>
  );
}

// Layout picker (sidebar-right / sidebar-left / topbar) — controls nav placement.
function LayoutCard() {
  const { layout, setLayout } = useConfig();
  const options: Array<{ key: Layout; label: string; description: string }> = [
    { key: "sidebar-right", label: "سایدبار راست", description: "چیدمان پیش‌فرض RTL" },
    { key: "sidebar-left", label: "سایدبار چپ", description: "منو در سمت چپ" },
    { key: "topbar", label: "منوی بالا", description: "ناوبری افقی در بالا" },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">چیدمان</CardTitle>
        <CardDescription>موقعیت قرارگیری منوی ناوبری</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={layout} onValueChange={(v) => setLayout(v as Layout)} className="grid grid-cols-3 gap-2">
          {options.map((o) => (
            <label
              key={o.key}
              className={`flex flex-col items-start gap-1 rounded-lg border p-3 cursor-pointer hover:bg-muted/40 transition-colors ${
                layout === o.key ? "border-primary bg-primary/5" : ""
              }`}
            >
              <RadioGroupItem value={o.key} className="sr-only" />
              <span className="text-sm font-medium">{o.label}</span>
              <span className="text-[10px] text-muted-foreground leading-tight">{o.description}</span>
            </label>
          ))}
        </RadioGroup>
      </CardContent>
    </Card>
  );
}

// Calendar mode (Jalali / Gregorian). Changing requires reload so all dates re-render.
function CalendarModeCard() {
  const { calendarMode, setCalendarMode } = useConfig();
  const [localMode, setLocalMode] = React.useState<CalendarMode>(calendarMode);
  React.useEffect(() => setLocalMode(calendarMode), [calendarMode]);
  const apply = (m: CalendarMode) => {
    setLocalMode(m);
    setCalendarMode(m);
    persistCalendarMode(m); // also persist to localStorage via calendar module
    if (typeof window !== "undefined") {
      window.localStorage.setItem("workshop_calendar", m);
      toast.info("تقویم تغییر یافت — صفحه برای اعمال تغییرات بارگذاری مجدد می‌شود…");
      setTimeout(() => window.location.reload(), 600);
    }
  };
  const options: Array<{ key: CalendarMode; label: string; description: string }> = [
    { key: "jalali", label: "شمسی", description: "تقویم Jalali پارسی" },
    { key: "gregorian", label: "میلادی", description: "تقویم میلادی ISO" },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">تقویم</CardTitle>
        <CardDescription>نوع تقویم نمایش تاریخ‌ها</CardDescription>
      </CardHeader>
      <CardContent>
        <RadioGroup value={localMode} onValueChange={(v) => apply(v as CalendarMode)} className="grid grid-cols-2 gap-2">
          {options.map((o) => (
            <label
              key={o.key}
              className={`flex flex-col items-start gap-1 rounded-lg border p-3 cursor-pointer hover:bg-muted/40 transition-colors ${
                localMode === o.key ? "border-primary bg-primary/5" : ""
              }`}
            >
              <RadioGroupItem value={o.key} className="sr-only" />
              <span className="text-sm font-medium">{o.label}</span>
              <span className="text-[10px] text-muted-foreground leading-tight">{o.description}</span>
            </label>
          ))}
        </RadioGroup>
        <p className="mt-2 text-[11px] text-muted-foreground">
          پس از تغییر، صفحه به‌صورت خودکار بارگذاری مجدد می‌شود تا همه تاریخ‌ها به‌روزرسانی شوند.
        </p>
      </CardContent>
    </Card>
  );
}

// Brand color picker — only enabled when theme=corporate.
function BrandColorCard() {
  const { theme, brandColor, setBrandColor } = useConfig();
  const disabled = theme !== "corporate";
  const presets = [
    "oklch(0.55 0.18 250)",   // blue
    "oklch(0.55 0.22 25)",    // red
    "oklch(0.5 0.18 145)",    // green
    "oklch(0.55 0.18 295)",   // purple
    "oklch(0.55 0.2 80)",     // amber
    "oklch(0.4 0.1 250)",     // navy
  ];
  return (
    <Card className={disabled ? "opacity-60" : undefined}>
      <CardHeader>
        <CardTitle className="text-base">رنگ برند</CardTitle>
        <CardDescription>
          {disabled ? "فقط در تم «شرکتی» فعال است" : "رنگ اصلی برند برای تم شرکتی"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <input
            type="color"
            disabled={disabled}
            value={oklchToHexOrFallback(brandColor, "#3b82f6")}
            onChange={(e) => setBrandColor(hexToOklch(e.target.value) ?? brandColor)}
            className="h-10 w-14 rounded-md border bg-background"
            aria-label="انتخاب رنگ"
          />
          <div className="flex flex-wrap gap-1.5">
            {presets.map((p) => (
              <button
                key={p}
                type="button"
                disabled={disabled}
                onClick={() => setBrandColor(p)}
                className={`h-7 w-7 rounded-full border-2 ${
                  brandColor === p ? "border-foreground" : "border-transparent"
                }`}
                style={{ background: p }}
                aria-label={`رنگ برند ${p}`}
              />
            ))}
          </div>
        </div>
        <p className="text-[11px] text-muted-foreground font-mono nums" dir="ltr">{brandColor}</p>
      </CardContent>
    </Card>
  );
}

// Small color-space conversion helpers (best-effort; oklch strings kept verbatim).
function oklchToHexOrFallback(oklch: string, fallback: string): string {
  // We do not run a full oklch→sRGB conversion here; instead expose the value
  // via the custom property so the user sees the live swatch. For the <input type=color>
  // we fall back to a hex that approximates the chosen preset.
  try {
    const m = oklch.match(/oklch\(([\d.]+)\s+([\d.]+)\s+([\d.]+)\)/);
    if (!m) return fallback;
    const [, l, c, h] = m;
    void l; void c;
    // crude hue→hex wheel
    const hue = parseFloat(h);
    return hslToHex(hue, 60, 45);
  } catch {
    return fallback;
  }
}
function hslToHex(h: number, s: number, l: number): string {
  s /= 100; l /= 100;
  const k = (n: number) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) => {
    const c = l - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1));
    return Math.round(255 * c).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}
function hexToOklch(hex: string): string | null {
  // Best-effort: keep presets in sync; otherwise just store the hex.
  if (!hex.startsWith("#")) return null;
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;
  let h = 0;
  if (max !== min) {
    const d = max - min;
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) * 60; break;
      case g: h = ((b - r) / d + 2) * 60; break;
      case b: h = ((r - g) / d + 4) * 60; break;
    }
  }
  // Use the legacy css color via approximated oklch
  return `oklch(${(0.4 + l * 0.5).toFixed(3)} 0.18 ${h.toFixed(1)})`;
}

function PanelDisplayCard() {
  const { title, iconKey, setTitle, setIconKey } = useConfig();
  const iconOptions: Array<{ key: IconKey; label: string; Icon: React.ComponentType<{ className?: string }> }> = [
    { key: "factory", label: "کارخانه", Icon: Factory },
    { key: "boxes", label: "جعبه‌ها", Icon: Boxes },
    { key: "package", label: "بسته", Icon: Package },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">تنظیمات نمایش پنل</CardTitle>
        <CardDescription>عنوان و آیکون پنل را به‌روز کنید</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="panel-title">عنوان پنل</Label>
          <Input
            id="panel-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="پنل کارگاه تولید و پخش"
          />
        </div>
        <div className="space-y-1.5">
          <Label>آیکون پنل</Label>
          <div className="grid grid-cols-3 gap-2">
            {iconOptions.map(({ key, label, Icon: OptionIcon }) => {
              const active = iconKey === key;
              const ActiveIcon = ICON_MAP[iconKey] ?? Factory;
              void ActiveIcon;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setIconKey(key)}
                  className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 transition-colors ${
                    active ? "border-primary bg-primary/5 text-primary" : "hover:bg-muted/40 text-muted-foreground"
                  }`}
                >
                  <OptionIcon className="h-5 w-5" />
                  <span className="text-xs">{label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ServerConnectionCard() {
  const [demo, setDemo] = React.useState(isDemoMode());
  const [reloading, setReloading] = React.useState(false);
  React.useEffect(() => {
    const unsub = (window as any);
    return () => void unsub;
  }, []);
  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  const onRetry = () => {
    setReloading(true);
    resetBackendProbe();
    toast.info("در حال تلاش مجدد برای اتصال به سرور…");
    setTimeout(() => {
      setReloading(false);
      setDemo(isDemoMode());
      if (!isDemoMode()) {
        toast.success("اتصال برقرار شد.");
      } else {
        toast.warning("سرور همچنان در دسترس نیست — حالت دمو فعال است.");
      }
    }, 1000);
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base"><ServerCog className="h-5 w-5" /> اتصال به سرور</CardTitle>
        <CardDescription>وضعیت اتصال به بک‌اند Django</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between rounded-lg border p-3">
          <div>
            <p className="text-sm font-medium">آدرس سرور</p>
            <p className="text-xs text-muted-foreground font-mono nums" dir="ltr">{host}:8000</p>
          </div>
          {demo ? (
            <Badge className="bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10">حالت دمو</Badge>
          ) : (
            <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10">متصل</Badge>
          )}
        </div>
        {demo && (
          <Alert>
            <ServerCog className="h-4 w-4" />
            <AlertTitle>حالت دمو فعال</AlertTitle>
            <AlertDescription>
              بک‌اند (Django روی پورت ۸۰۰۰) در دسترس نیست. داده‌ها از حافظه موقت خوانده می‌شوند.
            </AlertDescription>
          </Alert>
        )}
        <Button onClick={onRetry} disabled={reloading} variant="outline" className="w-full">
          {reloading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          تلاش مجدد
        </Button>
      </CardContent>
    </Card>
  );
}

function AboutCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">درباره سیستم</CardTitle>
        <CardDescription>اطلاعات نسخه و توضیحات</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">نسخه</p>
            <p className="font-semibold nums" dir="ltr">۱.۰.۰</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">تاریخ ساخت</p>
            <p className="font-semibold nums" dir="ltr">{new Date().toISOString().slice(0, 10)}</p>
          </div>
        </div>
        <Separator />
        <p className="text-sm text-muted-foreground leading-6">
          نرم‌افزار جامع مدیریت تولید و پخش — یکپارچه‌سازی تولید، انبار، فروش، حسابداری و پخش
          در یک پنل کاربردی با پشتیبانی کامل از زبان فارسی و چیدمان راست‌چین.
        </p>
      </CardContent>
    </Card>
  );
}

function SystemTab() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <PanelDisplayCard />
      <AppThemeCard />
      <LayoutCard />
      <CalendarModeCard />
      <BrandColorCard />
      <ThemeCard />
      <ServerConnectionCard />
      <AboutCard />
    </div>
  );
}

// ---------------------------------------------------------------------------
// 6) Units tab — مدیریت واحدها (CRUD)
// ---------------------------------------------------------------------------

interface Unit {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

function UnitFormDialog({
  open,
  onOpenChange,
  unit,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  unit: Unit | null;
  onSaved: () => void;
}) {
  const isEdit = unit !== null;
  const [code, setCode] = React.useState("");
  const [name, setName] = React.useState("");
  const [isActive, setIsActive] = React.useState(true);

  React.useEffect(() => {
    if (!open) return;
    if (unit) {
      setCode(unit.code);
      setName(unit.name);
      setIsActive(unit.is_active);
    } else {
      setCode("");
      setName("");
      setIsActive(true);
    }
  }, [open, unit]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const body = { code: code.trim(), name: name.trim(), is_active: isActive };
      if (isEdit) {
        return api<Unit>(`/products/units/${unit!.id}/`, { method: "PUT", body });
      }
      return api<Unit>("/products/units/", { method: "POST", body });
    },
    onSuccess: () => {
      toast.success(isEdit ? "واحد ویرایش شد." : "واحد ساخته شد.");
      onOpenChange(false);
      onSaved();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "ویرایش واحد" : "واحد جدید"}</DialogTitle>
          <DialogDescription>کد و نام واحد را وارد کنید (مثلاً: KG / کیلوگرم)</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="u-code">کد واحد</Label>
            <Input id="u-code" dir="ltr" className="nums" value={code} onChange={(e) => setCode(e.target.value)} placeholder="KG" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="u-name">نام واحد</Label>
            <Input id="u-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="کیلوگرم" />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">فعال</p>
              <p className="text-xs text-muted-foreground">آیا این واحد قابل استفاده است؟</p>
            </div>
            <Switch checked={isActive} onCheckedChange={setIsActive} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !code || !name}>
            {saveMutation.isPending ? "در حال ذخیره…" : isEdit ? "ذخیره تغییرات" : "افزودن"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function UnitsTab() {
  const qc = useQueryClient();
  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Unit | null>(null);
  const [deleting, setDeleting] = React.useState<Unit | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["units-list"],
    queryFn: () => api<Paginated<Unit>>("/products/units/", { query: { page: 1, page_size: 100 } }),
  });
  const units = data?.results ?? [];

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api(`/products/units/${id}/`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success("واحد حذف شد.");
      setDeleting(null);
      qc.invalidateQueries({ queryKey: ["units-list"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">مدیریت واحدها</CardTitle>
          <CardDescription>واحدهای اندازه‌گیری (عدد، کیلوگرم، گرم و ...)</CardDescription>
        </div>
        <Button onClick={() => { setEditing(null); setFormOpen(true); }}>
          <Plus className="h-4 w-4" /> افزودن واحد
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">کد</TableHead>
                <TableHead className="text-right">نام</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right w-24">عملیات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-8">در حال بارگذاری…</TableCell></TableRow>
              ) : units.length === 0 ? (
                <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-8">واحدی یافت نشد.</TableCell></TableRow>
              ) : (
                units.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-mono nums" dir="ltr">{u.code}</TableCell>
                    <TableCell className="font-medium">{u.name}</TableCell>
                    <TableCell>
                      {u.is_active ? (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10">
                          <CheckCircle2 className="h-3 w-3" /> فعال
                        </Badge>
                      ) : (
                        <Badge variant="secondary"><XCircle className="h-3 w-3" /> غیرفعال</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => { setEditing(u); setFormOpen(true); }}>ویرایش</Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => setDeleting(u)}
                        >حذف</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <UnitFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        unit={editing}
        onSaved={() => qc.invalidateQueries({ queryKey: ["units-list"] })}
      />
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(v) => !v && setDeleting(null)}
        title="حذف واحد"
        description={`آیا از حذف «${deleting?.name}» مطمئن هستید؟`}
        confirmText="حذف"
        tone="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 7) Warehouses tab — مدیریت انبارها (CRUD)
// ---------------------------------------------------------------------------

interface Warehouse {
  id: number;
  code: string;
  name: string;
  type: string;
  type_display?: string;
  is_active: boolean;
  contractor?: number | null;
  contractor_name?: string;
  store?: number | null;
  address?: string;
}

const WAREHOUSE_TYPE_LABELS: Record<string, string> = {
  main: "اصلی",
  raw_materials: "مواد اولیه",
  finished_goods: "محصولات",
  workshop: "کارگاه",
  store: "فروشگاه",
  virtual: "مجازی",
};

function WarehouseFormDialog({
  open,
  onOpenChange,
  warehouse,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  warehouse: Warehouse | null;
  onSaved: () => void;
}) {
  const isEdit = warehouse !== null;
  const [code, setCode] = React.useState("");
  const [name, setName] = React.useState("");
  const [type, setType] = React.useState("raw_materials");
  const [isActive, setIsActive] = React.useState(true);
  const [address, setAddress] = React.useState("");

  React.useEffect(() => {
    if (!open) return;
    if (warehouse) {
      setCode(warehouse.code);
      setName(warehouse.name);
      setType(warehouse.type);
      setIsActive(warehouse.is_active);
      setAddress(warehouse.address ?? "");
    } else {
      setCode("");
      setName("");
      setType("raw_materials");
      setIsActive(true);
      setAddress("");
    }
  }, [open, warehouse]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const body = {
        code: code.trim(),
        name: name.trim(),
        type,
        is_active: isActive,
        address,
      };
      if (isEdit) {
        return api<Warehouse>(`/inventory/warehouses/${warehouse!.id}/`, { method: "PUT", body });
      }
      return api<Warehouse>("/inventory/warehouses/", { method: "POST", body });
    },
    onSuccess: () => {
      toast.success(isEdit ? "انبار ویرایش شد." : "انبار ساخته شد.");
      onOpenChange(false);
      onSaved();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "ویرایش انبار" : "انبار جدید"}</DialogTitle>
          <DialogDescription>کد، نام و نوع انبار را مشخص کنید</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="w-code">کد</Label>
              <Input id="w-code" dir="ltr" className="nums" value={code} onChange={(e) => setCode(e.target.value)} placeholder="WH-RAW-01" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="w-type">نوع</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(WAREHOUSE_TYPE_LABELS).map(([k, v]) => (
                    <SelectItem key={k} value={k}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="w-name">نام</Label>
            <Input id="w-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="انبار مواد اولیه ۱" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="w-address">آدرس (اختیاری)</Label>
            <Textarea id="w-address" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="تهران - ..." />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">فعال</p>
              <p className="text-xs text-muted-foreground">آیا این انبار فعال است؟</p>
            </div>
            <Switch checked={isActive} onCheckedChange={setIsActive} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !code || !name}>
            {saveMutation.isPending ? "در حال ذخیره…" : isEdit ? "ذخیره تغییرات" : "افزودن"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function WarehousesTab() {
  const qc = useQueryClient();
  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Warehouse | null>(null);
  const [deleting, setDeleting] = React.useState<Warehouse | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["warehouses-list"],
    queryFn: () => api<Paginated<Warehouse>>("/inventory/warehouses/", { query: { page: 1, page_size: 200 } }),
  });
  const warehouses = data?.results ?? [];

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api(`/inventory/warehouses/${id}/`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success("انبار حذف شد.");
      setDeleting(null);
      qc.invalidateQueries({ queryKey: ["warehouses-list"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">مدیریت انبارها</CardTitle>
          <CardDescription>انبارهای مواد اولیه، محصولات، کارگاه و ...</CardDescription>
        </div>
        <Button onClick={() => { setEditing(null); setFormOpen(true); }}>
          <Plus className="h-4 w-4" /> افزودن انبار
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">کد</TableHead>
                <TableHead className="text-right">نام</TableHead>
                <TableHead className="text-right">نوع</TableHead>
                <TableHead className="text-right">کارپرداز</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right w-24">عملیات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">در حال بارگذاری…</TableCell></TableRow>
              ) : warehouses.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground py-8">انباری یافت نشد.</TableCell></TableRow>
              ) : (
                warehouses.map((w) => (
                  <TableRow key={w.id}>
                    <TableCell className="font-mono nums" dir="ltr">{w.code}</TableCell>
                    <TableCell className="font-medium">{w.name}</TableCell>
                    <TableCell><Badge variant="outline">{WAREHOUSE_TYPE_LABELS[w.type] ?? w.type}</Badge></TableCell>
                    <TableCell>{w.contractor_name ?? "—"}</TableCell>
                    <TableCell>
                      {w.is_active ? (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10">
                          <CheckCircle2 className="h-3 w-3" /> فعال
                        </Badge>
                      ) : (
                        <Badge variant="secondary"><XCircle className="h-3 w-3" /> غیرفعال</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => { setEditing(w); setFormOpen(true); }}>ویرایش</Button>
                        <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleting(w)}>حذف</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <WarehouseFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        warehouse={editing}
        onSaved={() => qc.invalidateQueries({ queryKey: ["warehouses-list"] })}
      />
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(v) => !v && setDeleting(null)}
        title="حذف انبار"
        description={`آیا از حذف «${deleting?.name}» مطمئن هستید؟`}
        confirmText="حذف"
        tone="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// 8) Employees tab — مدیریت کارکنان (CRUD)
// ---------------------------------------------------------------------------

interface Employee {
  id: number;
  code: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  national_id?: string;
  mobile?: string;
  phone?: string;
  position: string;
  workshop?: number | null;
  workshop_name?: string;
  hire_date: string;
  is_active: boolean;
}

function EmployeeFormDialog({
  open,
  onOpenChange,
  employee,
  warehouses,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  employee: Employee | null;
  warehouses: Warehouse[];
  onSaved: () => void;
}) {
  const isEdit = employee !== null;
  const [code, setCode] = React.useState("");
  const [firstName, setFirstName] = React.useState("");
  const [lastName, setLastName] = React.useState("");
  const [nationalId, setNationalId] = React.useState("");
  const [mobile, setMobile] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [position, setPosition] = React.useState("");
  const [workshopId, setWorkshopId] = React.useState<string>("");
  const [hireDate, setHireDate] = React.useState<string | null>(todayISO());
  const [isActive, setIsActive] = React.useState(true);

  React.useEffect(() => {
    if (!open) return;
    if (employee) {
      setCode(employee.code);
      setFirstName(employee.first_name);
      setLastName(employee.last_name);
      setNationalId(employee.national_id ?? "");
      setMobile(employee.mobile ?? "");
      setPhone(employee.phone ?? "");
      setPosition(employee.position);
      setWorkshopId(employee.workshop ? String(employee.workshop) : "");
      setHireDate(employee.hire_date);
      setIsActive(employee.is_active);
    } else {
      setCode("");
      setFirstName("");
      setLastName("");
      setNationalId("");
      setMobile("");
      setPhone("");
      setPosition("");
      setWorkshopId("");
      setHireDate(todayISO());
      setIsActive(true);
    }
  }, [open, employee]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const body = {
        code: code.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        national_id: nationalId.trim(),
        mobile: mobile.trim(),
        phone: phone.trim(),
        position: position.trim(),
        workshop: workshopId ? Number(workshopId) : null,
        hire_date: hireDate,
        is_active: isActive,
      };
      if (isEdit) {
        return api<Employee>(`/workshop/employees/${employee!.id}/`, { method: "PUT", body });
      }
      return api<Employee>("/workshop/employees/", { method: "POST", body });
    },
    onSuccess: () => {
      toast.success(isEdit ? "کارکنان ویرایش شد." : "کارکنان ساخته شد.");
      onOpenChange(false);
      onSaved();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  // Only show warehouses of type=workshop as candidate workshop for employees
  const workshopOptions = warehouses.filter((w) => w.type === "workshop");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "ویرایش کارکنان" : "کارکنان جدید"}</DialogTitle>
          <DialogDescription>اطلاعات کامل کارکنان را وارد کنید</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="e-code">کد</Label>
              <Input id="e-code" dir="ltr" className="nums" value={code} onChange={(e) => setCode(e.target.value)} placeholder="EMP-001" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="e-position">سمت</Label>
              <Input id="e-position" value={position} onChange={(e) => setPosition(e.target.value)} placeholder="مسئول کارگاه" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="e-first">نام</Label>
              <Input id="e-first" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="e-last">نام خانوادگی</Label>
              <Input id="e-last" value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="e-national">کد ملی</Label>
              <Input id="e-national" dir="ltr" className="nums" value={nationalId} onChange={(e) => setNationalId(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="e-mobile">موبایل</Label>
              <Input id="e-mobile" dir="ltr" className="nums" value={mobile} onChange={(e) => setMobile(e.target.value)} placeholder="0912..." />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="e-phone">تلفن ثابت</Label>
              <Input id="e-phone" dir="ltr" className="nums" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="e-workshop">کارگاه</Label>
              <Select value={workshopId} onValueChange={setWorkshopId}>
                <SelectTrigger><SelectValue placeholder="بدون کارگاه" /></SelectTrigger>
                <SelectContent>
                  {workshopOptions.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>{w.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>تاریخ شروع به کار</Label>
            <DatePicker value={hireDate} onChange={setHireDate} />
          </div>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">فعال</p>
              <p className="text-xs text-muted-foreground">آیا این کارکنان فعال است؟</p>
            </div>
            <Switch checked={isActive} onCheckedChange={setIsActive} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !code || !firstName || !lastName || !position}>
            {saveMutation.isPending ? "در حال ذخیره…" : isEdit ? "ذخیره تغییرات" : "افزودن"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function EmployeesTab() {
  const qc = useQueryClient();
  const [formOpen, setFormOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Employee | null>(null);
  const [deleting, setDeleting] = React.useState<Employee | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["employees-list"],
    queryFn: () => api<Paginated<Employee>>("/workshop/employees/", { query: { page: 1, page_size: 100 } }),
  });
  const employees = data?.results ?? [];

  // Fetch warehouses for the workshop select dropdown
  const { data: warehousesData } = useQuery({
    queryKey: ["warehouses-list-for-employees"],
    queryFn: () => api<Paginated<Warehouse>>("/inventory/warehouses/", { query: { page: 1, page_size: 100 } }),
  });
  const warehouses = warehousesData?.results ?? [];

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api(`/workshop/employees/${id}/`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success("کارکنان حذف شد.");
      setDeleting(null);
      qc.invalidateQueries({ queryKey: ["employees-list"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">مدیریت کارکنان</CardTitle>
          <CardDescription>پرسنل کارگاه‌ها — کارگر، انباردار، مسئول کارگاه</CardDescription>
        </div>
        <Button onClick={() => { setEditing(null); setFormOpen(true); }}>
          <Plus className="h-4 w-4" /> افزودن کارکنان
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto scroll-pretty">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-right">کد</TableHead>
                <TableHead className="text-right">نام کامل</TableHead>
                <TableHead className="text-right">سمت</TableHead>
                <TableHead className="text-right">موبایل</TableHead>
                <TableHead className="text-right">کارگاه</TableHead>
                <TableHead className="text-right">وضعیت</TableHead>
                <TableHead className="text-right w-24">عملیات</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">در حال بارگذاری…</TableCell></TableRow>
              ) : employees.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">کارکنانی یافت نشد.</TableCell></TableRow>
              ) : (
                employees.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell className="font-mono nums" dir="ltr">{e.code}</TableCell>
                    <TableCell className="font-medium">{e.full_name ?? `${e.first_name} ${e.last_name}`}</TableCell>
                    <TableCell>{e.position}</TableCell>
                    <TableCell className="font-mono nums" dir="ltr">{e.mobile ?? "—"}</TableCell>
                    <TableCell>{e.workshop_name ?? "—"}</TableCell>
                    <TableCell>
                      {e.is_active ? (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10">
                          <CheckCircle2 className="h-3 w-3" /> فعال
                        </Badge>
                      ) : (
                        <Badge variant="secondary"><XCircle className="h-3 w-3" /> غیرفعال</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={() => { setEditing(e); setFormOpen(true); }}>ویرایش</Button>
                        <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleting(e)}>حذف</Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <EmployeeFormDialog
        open={formOpen}
        onOpenChange={setFormOpen}
        employee={editing}
        warehouses={warehouses}
        onSaved={() => qc.invalidateQueries({ queryKey: ["employees-list"] })}
      />
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(v) => !v && setDeleting(null)}
        title="حذف کارکنان"
        description={`آیا از حذف «${deleting?.full_name ?? `${deleting?.first_name ?? ""} ${deleting?.last_name ?? ""}`.trim()}» مطمئن هستید؟`}
        confirmText="حذف"
        tone="destructive"
        loading={deleteMutation.isPending}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
      />
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export function SettingsView() {
  return (
    <div className="space-y-4">
      <Tabs defaultValue="profile">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="profile"><UserIcon className="h-4 w-4" /> پروفایل</TabsTrigger>
          <TabsTrigger value="users"><UserIcon className="h-4 w-4" /> کاربران</TabsTrigger>
          <TabsTrigger value="company"><Building2 className="h-4 w-4" /> شرکت</TabsTrigger>
          <TabsTrigger value="roles"><Shield className="h-4 w-4" /> نقش‌ها</TabsTrigger>
          <TabsTrigger value="units"><Package className="h-4 w-4" /> واحدها</TabsTrigger>
          <TabsTrigger value="warehouses"><Factory className="h-4 w-4" /> انبارها</TabsTrigger>
          <TabsTrigger value="employees"><UserIcon className="h-4 w-4" /> کارکنان</TabsTrigger>
          <TabsTrigger value="system"><ServerCog className="h-4 w-4" /> سیستم</TabsTrigger>
        </TabsList>
        <TabsContent value="profile" className="mt-4"><ProfileTab /></TabsContent>
        <TabsContent value="users" className="mt-4"><UsersTab /></TabsContent>
        <TabsContent value="company" className="mt-4"><CompanyTab /></TabsContent>
        <TabsContent value="roles" className="mt-4"><RolesTab /></TabsContent>
        <TabsContent value="units" className="mt-4"><UnitsTab /></TabsContent>
        <TabsContent value="warehouses" className="mt-4"><WarehousesTab /></TabsContent>
        <TabsContent value="employees" className="mt-4"><EmployeesTab /></TabsContent>
        <TabsContent value="system" className="mt-4"><SystemTab /></TabsContent>
      </Tabs>
    </div>
  );
}
