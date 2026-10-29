"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Truck, Loader2, Lock, User, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { useDistributorAuthStore } from "@/store/distributor-auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function DistributorLogin() {
  const { login } = useDistributorAuthStore();
  const [username, setUsername] = React.useState("distributor1");
  const [password, setPassword] = React.useState("Distributor@123");
  const [loading, setLoading] = React.useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error("نام کاربری و گذرواژه را وارد کنید.");
      return;
    }
    setLoading(true);
    try {
      await login(username, password);
      toast.success("ورود موفقیت‌آمیز بود. خوش آمدید!");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "خطا در ورود.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      dir="rtl"
      className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-emerald-100 via-emerald-50 to-background p-4"
    >
      <div
        className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-emerald-300/30 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-teal-300/30 blur-3xl"
        aria-hidden
      />
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative w-full max-w-md"
      >
        <Card className="border-emerald-200/60 shadow-xl">
          <CardHeader className="text-center space-y-3 pb-2">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-lg">
              <Truck className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-2xl">اپلیکیشن عامل پخش</CardTitle>
              <CardDescription className="text-sm">
                برای ثبت فروش و مشاهده گزارش‌ها وارد شوید.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <form onSubmit={onSubmit} className="space-y-4" autoComplete="off">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">
                  نام کاربری
                </Label>
                <div className="relative">
                  <User className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="h-12 pr-9 text-base"
                    placeholder="distributor1"
                    autoComplete="username"
                    dir="ltr"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">
                  گذرواژه
                </Label>
                <div className="relative">
                  <Lock className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-12 pr-9 text-base"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    dir="ltr"
                  />
                </div>
              </div>
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 text-base bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    در حال ورود…
                  </>
                ) : (
                  "ورود به اپلیکیشن"
                )}
              </Button>
            </form>
            <div className="rounded-lg border border-dashed border-emerald-300 bg-emerald-50/40 px-3 py-2 text-center text-xs text-muted-foreground">
              کاربر آزمایشی:{" "}
              <span className="font-mono nums text-emerald-700" dir="ltr">
                distributor1 / Distributor@123
              </span>
            </div>
            <a
              href="/"
              className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground hover:text-emerald-700 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              ورود به پنل مدیریت
            </a>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
