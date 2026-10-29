"use client";

import * as React from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Plus, Eye, MoreHorizontal, Scale } from "lucide-react";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_JOURNALS, MOCK_ACCOUNTS } from "@/lib/mock-data";
import { formatDate, formatRial } from "@/lib/format";
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

type Journal = (typeof MOCK_JOURNALS)[number];
type Account = (typeof MOCK_ACCOUNTS)[number];

const STATUS_LABEL: Record<string, string> = {
  draft: "پیش‌نویس",
  posted: "ثبت‌شده",
  reversed: "برگشت‌خورده",
};

function JournalDetailsDialog({ journal, onOpenChange }: { journal: Journal | null; onOpenChange: (v: boolean) => void }) {
  // وقتی کاربر روی «مشاهده خطوط» کلیک می‌کنه، journal اطلاعات پایه‌ای رو داره
  // ولی lines توش نیست (لست endpoint خطوط رو برنمی‌گردونه). پس باید endpoint
  // جزئیات رو صدا بزنیم تا خطوط رو بگیریم.
  const { data: detail, isLoading } = useQuery({
    queryKey: ["journal-detail", journal?.id],
    queryFn: () => api<Journal & { lines: Array<{ id: number; account: number; account_code: string; account_name: string; debit: string; credit: string; description?: string }> }>(`/accounting/journals/${journal!.id}/`),
    enabled: journal !== null,
  });

  const lines = detail?.lines ?? [];

  return (
    <Dialog open={journal !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>سند {journal?.journal_no}</DialogTitle>
          <DialogDescription>{journal?.description}</DialogDescription>
        </DialogHeader>
        {journal && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div><p className="text-xs text-muted-foreground">تاریخ</p><p className="font-medium nums" dir="ltr">{formatDate(journal.date)}</p></div>
              <div><p className="text-xs text-muted-foreground">جمع بده</p><p className="font-semibold nums">{formatRial(journal.total_debit)}</p></div>
              <div><p className="text-xs text-muted-foreground">جمع بستانکار</p><p className="font-semibold nums">{formatRial(journal.total_credit)}</p></div>
            </div>
            <div className="rounded-lg border overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">حساب</TableHead>
                    <TableHead className="text-right">کد</TableHead>
                    <TableHead className="text-right">بده</TableHead>
                    <TableHead className="text-right">بستانکار</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-4">در حال بارگذاری خطوط…</TableCell></TableRow>
                  ) : lines.length === 0 ? (
                    <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground py-4">خطوطی یافت نشد.</TableCell></TableRow>
                  ) : (
                    lines.map((l: any) => (
                      <TableRow key={l.id}>
                        <TableCell className="font-medium">{l.account_name ?? `حساب #${l.account}`}</TableCell>
                        <TableCell className="font-mono nums" dir="ltr">{l.account_code}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(l.debit)}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatRial(l.credit)}</TableCell>
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

function ManualJournalDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const qc = useQueryClient();
  const [date, setDate] = React.useState(new Date().toISOString().slice(0, 10));
  const [description, setDescription] = React.useState("");
  const [lines, setLines] = React.useState<Array<{ account_id: string; debit: string; credit: string }>>([
    { account_id: "", debit: "0", credit: "0" },
    { account_id: "", debit: "0", credit: "0" },
  ]);

  const { data: accountsData } = useQuery({
    queryKey: ["accounts-list"],
    queryFn: () => api<Account[] | { results: Account[] }>("/accounting/accounts/"),
    enabled: open,
  });
  const accounts = React.useMemo<Account[]>(() => {
    if (!accountsData) return [];
    if (Array.isArray(accountsData)) return accountsData;
    return accountsData.results ?? [];
  }, [accountsData]);

  const totalDebit = lines.reduce((s, l) => s + (parseFloat(l.debit) || 0), 0);
  const totalCredit = lines.reduce((s, l) => s + (parseFloat(l.credit) || 0), 0);
  const balanced = Math.abs(totalDebit - totalCredit) < 0.01 && totalDebit > 0;

  const addLine = () => setLines((l) => [...l, { account_id: "", debit: "0", credit: "0" }]);
  const removeLine = (i: number) => setLines((l) => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, patch: Partial<{ account_id: string; debit: string; credit: string }>) =>
    setLines((l) => l.map((line, idx) => (idx === i ? { ...line, ...patch } : line)));

  const mutation = useMutation({
    mutationFn: () =>
      api("/accounting/journals/create_manual/", {
        method: "POST",
        body: {
          date,
          description,
          lines: lines.map((l) => ({
            account_id: Number(l.account_id),
            debit: l.debit,
            credit: l.credit,
          })),
        },
      }),
    onSuccess: () => {
      toast.success("سند حسابداری ثبت شد.");
      qc.invalidateQueries({ queryKey: ["journals"] });
      setDescription("");
      setLines([{ account_id: "", debit: "0", credit: "0" }, { account_id: "", debit: "0", credit: "0" }]);
      onOpenChange(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>سند حسابداری دستی</DialogTitle>
          <DialogDescription>سند با خطوط بده/بستانکار ایجاد کنید. سند باید تراز باشد.</DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="j-date">تاریخ</Label>
            <Input id="j-date" type="date" dir="ltr" className="nums" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="j-desc">شرح</Label>
            <Input id="j-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="مثلاً: ثبت فروش نقدی" />
          </div>
        </div>

        <div className="rounded-lg border">
          <div className="grid grid-cols-[1fr_120px_140px_140px_40px] gap-2 border-b bg-muted/40 px-3 py-2 text-xs font-medium text-muted-foreground">
            <span>حساب</span>
            <span className="text-right">بده</span>
            <span className="text-right">بستانکار</span>
            <span />
          </div>
          <div className="max-h-64 overflow-y-auto scroll-pretty">
            {lines.map((l, i) => (
              <div key={i} className="grid grid-cols-[1fr_120px_140px_140px_40px] gap-2 border-b last:border-0 px-3 py-2">
                <Select value={l.account_id} onValueChange={(v) => updateLine(i, { account_id: v })}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="حساب" /></SelectTrigger>
                  <SelectContent>
                    {accounts?.map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>{a.code} — {a.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input className="h-9 nums" dir="ltr" value={l.debit} onChange={(e) => updateLine(i, { debit: e.target.value })} type="number" />
                <Input className="h-9 nums" dir="ltr" value={l.credit} onChange={(e) => updateLine(i, { credit: e.target.value })} type="number" />
                <Button variant="ghost" size="icon" onClick={() => removeLine(i)} disabled={lines.length <= 2} aria-label="حذف خط">
                  <Plus className="h-4 w-4 rotate-45" />
                </Button>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between px-3 py-2">
            <Button variant="outline" size="sm" onClick={addLine}>
              <Plus className="h-4 w-4" /> افزودن خط
            </Button>
            <div className="flex items-center gap-3 text-sm">
              <span className="nums">بده: {formatRial(totalDebit)}</span>
              <span className="nums">بستانکار: {formatRial(totalCredit)}</span>
              <Badge variant={balanced ? "default" : "destructive"}>
                <Scale className="h-3 w-3" />
                {balanced ? "تراز" : "ناتراز"}
              </Badge>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !balanced}>
            {mutation.isPending ? "در حال ثبت…" : "ثبت سند"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function AccountingView() {
  const [search, setSearch] = React.useState("");
  const debounced = useDebounced(search);
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [createOpen, setCreateOpen] = React.useState(false);
  const [viewing, setViewing] = React.useState<Journal | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["journals", { page, page_size: pageSize, search: debounced }],
    queryFn: () =>
      api<Paginated<Journal>>("/accounting/journals/", {
        query: { page, page_size: pageSize, search: debounced || undefined },
      }),
  });

  React.useEffect(() => setPage(1), [debounced]);

  const journals = data?.results ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>مدیریت حسابداری</CardTitle>
            <CardDescription>سندهای حسابداری به همراه خطوط بده و بستانکار</CardDescription>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            سند دستی
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <div className="p-4">
            <SearchInput value={search} onChange={setSearch} placeholder="جستجو بر اساس شماره سند…" className="sm:max-w-xs" />
          </div>
          <div className="overflow-x-auto scroll-pretty">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-right">شماره سند</TableHead>
                  <TableHead className="text-right">تاریخ</TableHead>
                  <TableHead className="text-right">شرح</TableHead>
                  <TableHead className="text-right">جمع بده</TableHead>
                  <TableHead className="text-right">جمع بستانکار</TableHead>
                  <TableHead className="text-right">وضعیت</TableHead>
                  <TableHead className="text-right w-16">عملیات</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow><TableCell colSpan={7} className="p-0"><TableSkeleton rows={8} cols={7} /></TableCell></TableRow>
                ) : journals.length === 0 ? (
                  <TableRow><TableCell colSpan={7}><EmptyState /></TableCell></TableRow>
                ) : (
                  journals.map((j) => (
                    <TableRow key={j.id}>
                      <TableCell className="font-mono nums" dir="ltr">{j.journal_no}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatDate(j.date)}</TableCell>
                      <TableCell className="font-medium max-w-xs truncate">{j.description}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(j.total_debit)}</TableCell>
                      <TableCell className="nums" dir="ltr">{formatRial(j.total_credit)}</TableCell>
                      <TableCell><Badge variant="secondary">{STATUS_LABEL[j.status] ?? j.status}</Badge></TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label="عملیات"><MoreHorizontal className="h-4 w-4" /></Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => setViewing(j)}>
                              <Eye className="h-4 w-4" />
                              مشاهده خطوط
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

      <ManualJournalDialog open={createOpen} onOpenChange={setCreateOpen} />
      <JournalDetailsDialog journal={viewing} onOpenChange={(v) => !v && setViewing(null)} />
    </div>
  );
}
