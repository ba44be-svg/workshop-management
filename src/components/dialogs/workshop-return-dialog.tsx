"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, type Paginated } from "@/lib/api";
import { MOCK_WORKSHOP_ISSUES } from "@/lib/mock-data";
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

type Issue = (typeof MOCK_WORKSHOP_ISSUES)[number];
type IssueLine = Issue["lines"][number];

interface ReturnLine {
  issue_line_id: number;
  product_name: string;
  qty_issued: string;
  qty_returned: string;
  remaining: string;
}

interface WorkshopReturnDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

const STEPS = [
  { id: 1, label: "سربرگ برگشت" },
  { id: 2, label: "اقلام برگشتی" },
  { id: 3, label: "خلاصه و ثبت" },
];

export function WorkshopReturnDialog({ open, onOpenChange }: WorkshopReturnDialogProps) {
  const qc = useQueryClient();
  const [step, setStep] = React.useState(1);
  const [returnDate, setReturnDate] = React.useState<string | null>(todayISO());
  const [issueId, setIssueId] = React.useState<string>("");
  const [reason, setReason] = React.useState("");
  const [lines, setLines] = React.useState<ReturnLine[]>([]);

  const { data: issues } = useQuery({
    queryKey: ["workshop-issues-options"],
    queryFn: () => api<Paginated<Issue>>("/workshop/issues/", { query: { page: 1, page_size: 50 } }),
  });
  const issueList = issues?.results ?? MOCK_WORKSHOP_ISSUES;
  const selectedIssue = issueList.find((i) => i.id === Number(issueId));

  React.useEffect(() => {
    if (selectedIssue) {
      setLines(
        selectedIssue.lines.map((l) => ({
          issue_line_id: l.id,
          product_name: l.product_name ?? "—",
          qty_issued: l.qty,
          qty_returned: "0",
          remaining: l.qty,
        }))
      );
    }
  }, [issueId]);

  const totalReturn = lines.reduce((s, l) => s + parseFloat(l.qty_returned || "0"), 0);
  const totalReturnValue = lines.reduce((s, l) => {
    const line = selectedIssue?.lines.find((x) => x.id === l.issue_line_id);
    if (!line) return s;
    return s + parseFloat(l.qty_returned) * parseFloat(line.unit_cost);
  }, 0);

  const createReturn = useMutation({
    mutationFn: () => {
      if (!selectedIssue) throw new Error("حواله را انتخاب کنید.");
      return api("/workshop/returns/create_return/", {
        method: "POST",
        body: {
          return_date: returnDate,
          issue: Number(issueId),
          contractor: selectedIssue.contractor,
          from_warehouse: selectedIssue.to_warehouse,
          to_warehouse: selectedIssue.from_warehouse,
          reason,
          lines: lines
            .filter((l) => parseFloat(l.qty_returned) > 0)
            .map((l) => ({
              issue_line: l.issue_line_id,
              qty: l.qty_returned,
            })),
        },
      });
    },
    onSuccess: () => {
      toast.success("برگشت از کارگاه ثبت شد.");
      qc.invalidateQueries({ queryKey: ["workshop-returns"] });
      onOpenChange(false);
      reset();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const reset = () => {
    setStep(1);
    setReturnDate(todayISO());
    setIssueId("");
    setReason("");
    setLines([]);
  };

  const canStep1 = returnDate && issueId && reason;
  const canStep2 = lines.length > 0 && lines.every((l) => parseFloat(l.qty_returned) <= parseFloat(l.qty_issued));

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) reset(); }}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>برگشت از کارگاه</DialogTitle>
          <DialogDescription>ثبت برگشت مواد اولیه از کارگاه کارپرداز به انبار</DialogDescription>
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
              <Label>تاریخ برگشت</Label>
              <DatePicker value={returnDate} onChange={setReturnDate} />
            </div>
            <div className="space-y-1.5">
              <Label>حواله مرجع</Label>
              <Select value={issueId} onValueChange={setIssueId}>
                <SelectTrigger><SelectValue placeholder="انتخاب حواله" /></SelectTrigger>
                <SelectContent>
                  {issueList.map((i) => (
                    <SelectItem key={i.id} value={String(i.id)}>{i.issue_no} — {i.contractor_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="ret-reason">دلیل برگشت</Label>
              <Textarea id="ret-reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="مثلاً: مقدار اضافی تحویلی، افت کیفیت" />
            </div>
            {selectedIssue && (
              <div className="sm:col-span-2 rounded-md border p-3 text-xs space-y-1">
                <div className="flex justify-between"><span className="text-muted-foreground">حواله</span><span className="font-mono nums">{selectedIssue.issue_no}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">کارپرداز</span><span>{selectedIssue.contractor_name}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">مبدأ→مقصد</span><span>{selectedIssue.from_warehouse} → {selectedIssue.to_warehouse}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">تعداد اقلام</span><span className="nums">{selectedIssue.lines_count}</span></div>
              </div>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <div className="overflow-x-auto scroll-pretty">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">محصول</TableHead>
                    <TableHead className="text-right">مقدار صادرشده</TableHead>
                    <TableHead className="text-right">مقدار برگشتی</TableHead>
                    <TableHead className="text-right">باقیمانده</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((l, idx) => {
                    const issued = parseFloat(l.qty_issued);
                    const ret = parseFloat(l.qty_returned);
                    const remaining = Math.max(0, issued - ret);
                    return (
                      <TableRow key={l.issue_line_id}>
                        <TableCell>{l.product_name}</TableCell>
                        <TableCell className="nums" dir="ltr">{formatNumber(l.qty_issued)}</TableCell>
                        <TableCell>
                          <Input
                            dir="ltr"
                            className="nums w-24"
                            type="number"
                            min="0"
                            max={l.qty_issued}
                            value={l.qty_returned}
                            onChange={(e) => {
                              const v = e.target.value;
                              setLines((prev) => prev.map((x, i) => i === idx ? { ...x, qty_returned: v, remaining: String(Math.max(0, issued - parseFloat(v || "0"))) } : x));
                            }}
                          />
                        </TableCell>
                        <TableCell className="nums" dir="ltr">
                          <Badge variant={ret > issued ? "destructive" : "outline"}>
                            {formatNumber(remaining)}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            {lines.some((l) => parseFloat(l.qty_returned) > parseFloat(l.qty_issued)) && (
              <p className="text-xs text-destructive">مقدار برگشتی نمی‌تواند از مقدار صادرشده بیشتر باشد.</p>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><p className="text-xs text-muted-foreground">تاریخ</p><p className="font-medium nums" dir="ltr">{formatDate(returnDate)}</p></div>
              <div><p className="text-xs text-muted-foreground">حواله</p><p className="font-medium nums" dir="ltr">{selectedIssue?.issue_no ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">کارپرداز</p><p className="font-medium">{selectedIssue?.contractor_name ?? "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">دلیل</p><p className="font-medium">{reason || "—"}</p></div>
              <div><p className="text-xs text-muted-foreground">مقدار برگشتی کل</p><p className="font-medium nums">{formatNumber(totalReturn)}</p></div>
              <div><p className="text-xs text-muted-foreground">ارزش برگشتی</p><p className="font-medium nums">{formatRial(totalReturnValue)}</p></div>
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
              <Button onClick={() => createReturn.mutate()} disabled={createReturn.isPending || !canStep2}>
                {createReturn.isPending ? "در حال ثبت…" : "ثبت برگشت"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
