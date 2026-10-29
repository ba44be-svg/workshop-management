/**
 * تبدیل عدد به حروف فارسی
 * نمونه: 150000000 → «یکصد و پنجاه میلیون»
 */

const ONES = [
  "", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه",
  "ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده",
  "هفده", "هجده", "نوزده",
];

const TENS = [
  "", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود",
];

const HUNDREDS = [
  "", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد",
];

const SCALES = [
  "", "هزار", "میلیون", "میلیارد", "هزار میلیارد", "بیلیون", "هزار بیلیون",
];

/**
 * تبدیل یک عدد سه‌رقم‌ی به حروف
 */
function threeDigitsToWords(n: number): string {
  if (n === 0) return "";
  const parts: string[] = [];
  const h = Math.floor(n / 100);
  const rem = n % 100;
  if (h > 0) {
    parts.push(HUNDREDS[h]);
  }
  if (rem > 0) {
    if (rem < 20) {
      parts.push(ONES[rem]);
    } else {
      const t = Math.floor(rem / 10);
      const o = rem % 10;
      parts.push(TENS[t]);
      if (o > 0) parts.push(ONES[o]);
    }
  }
  return parts.join(" و ");
}

/**
 * تبدیل عدد به حروف فارسی
 * @param num عدد (number یا string)
 * @returns حروف فارسی
 *
 * نمونه:
 *   numberToPersianWords(150) → "یکصد و پنجاه"
 *   numberToPersianWords(150000000) → "یکصد و پنجاه میلیون"
 *   numberToPersianWords(0) → "صفر"
 */
export function numberToPersianWords(num: number | string): string {
  let n: number;
  if (typeof num === "string") {
    n = parseInt(num.replace(/[^\d.-]/g, ""), 10);
  } else {
    n = num;
  }
  if (isNaN(n)) return "";
  if (n === 0) return "صفر";

  const isNegative = n < 0;
  n = Math.abs(Math.floor(n));

  // بخش اعشاری (اگه هست)
  // برای سادگی، فقط بخش صحیح رو تبدیل می‌کنیم

  if (n < 10) return ONES[n];
  if (n < 100) {
    const t = Math.floor(n / 10);
    const o = n % 10;
    return o > 0 ? `${TENS[t]} و ${ONES[o]}` : TENS[t];
  }

  const groups: number[] = [];
  while (n > 0) {
    groups.push(n % 1000);
    n = Math.floor(n / 1000);
  }

  const parts: string[] = [];
  for (let i = groups.length - 1; i >= 0; i--) {
    const g = groups[i];
    if (g === 0) continue;
    const words = threeDigitsToWords(g);
    const scale = SCALES[i] || "";
    parts.push(scale ? `${words} ${scale}` : words);
  }

  let result = parts.join(" و ");
  if (isNegative) result = "منفی " + result;
  return result;
}

/**
 * تبدیل مبلغ به حروف با «ریال» در آخر
 * نمونه: 150000000 → «یکصد و پنجاه میلیون ریال»
 */
export function amountToPersianWords(amount: number | string): string {
  const words = numberToPersianWords(amount);
  if (!words) return "";
  return `${words} ریال`;
}
