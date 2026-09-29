import { getCurrency, getLanguage, type Language } from "@/lib/i18n";

/** Maps our app language to the Intl locale used for number/date formatting. */
export function getIntlLocale(language: Language = getLanguage()): string {
  return language === "ru" ? "ru-RU" : "en-US";
}

/** Kyrgyz som mark: Cyrillic "с" with a low underline — the familiar local
 * glyph (like "$" for USD). Prefer this over bare "KGS" or the rarely-fonted
 * U+20C0 SOM SIGN, which often falls back to tofu or the ISO code. */
const SOM_SIGN = "с\u0332";

/** Builds the currency formatter every money helper here shares, so amounts
 * are labelled identically everywhere in the app.
 *
 * `currencyDisplay: "narrowSymbol"` avoids Intl's default "symbol" mode,
 * which prefixes symbols it considers ambiguous with a region marker — CNY
 * renders as "CN¥", HKD as "HK$" (both are in lib/currency.ts's supported
 * list) — reading like a typo next to the amount. narrowSymbol drops that
 * prefix (plain "¥", "$") while leaving every unambiguous currency (USD,
 * EUR, RUB, ...) exactly as compact as plain "symbol" already renders them
 * — unlike currencyDisplay: "code", which would fix CNY/HKD but turn every
 * other currency's "$1,234"/"1 234 ₽" into "USD 1,234"/"1 234 RUB". */
function createCurrencyFormatter(
  currency: string,
  maximumFractionDigits: number,
  minimumFractionDigits?: number,
): Intl.NumberFormat {
  return new Intl.NumberFormat(getIntlLocale(), {
    style: "currency",
    currency,
    currencyDisplay: "narrowSymbol",
    maximumFractionDigits,
    minimumFractionDigits: minimumFractionDigits ?? Math.min(2, maximumFractionDigits),
  });
}

/** Forces the underlined-с som mark wherever Intl emitted KGS / U+20C0. */
function applyCurrencyGlyphOverrides(formatted: string, currency: string): string {
  if (currency.toUpperCase() !== "KGS") return formatted;
  return formatted.replace(/\u20C0/g, SOM_SIGN).replace(/\bKGS\b/g, SOM_SIGN);
}

/** Narrow symbol for a currency code — ⃀ for KGS, ₽ for RUB, $ for USD, etc.
 * Used next to account names where the amount isn't being formatted. */
export function getCurrencySymbol(currency: string): string {
  const code = currency.toUpperCase();
  if (code === "KGS") return SOM_SIGN;
  const part = createCurrencyFormatter(code, 0)
    .formatToParts(0)
    .find((entry) => entry.type === "currency");
  return part?.value && part.value !== code ? part.value : code;
}

// `currency` defaults to the app's primary currency setting (Settings page)
// — call sites only need to pass it explicitly when formatting a value known
// to be in a *different* currency than that setting (e.g. an account balance
// or a transaction on a foreign-currency account).
//
// Always shows 2 fraction digits (kopecks / tyiyn / cents) — matches the
// backend Numeric(14, 2) scale and the transaction form's step="0.01".
export function formatCurrency(amount: number | string, currency: string = getCurrency()): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  return applyCurrencyGlyphOverrides(createCurrencyFormatter(currency, 2, 2).format(value), currency);
}

/** Same currency formatting as formatCurrency, but scales decimal precision
 * down to the value's own magnitude for tiny crypto prices — a low-cap
 * memecoin can genuinely price at $0.000000006894, and two fraction digits
 * would render that as "$0.00". Values >= 1 still show 2 decimals. */
export function formatCryptoAmount(amount: number | string, currency: string = getCurrency()): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  const abs = Math.abs(value);
  const maximumFractionDigits =
    abs === 0 || abs >= 1
      ? 2
      : // Leading zeros right after the decimal point before the first
        // significant digit, plus 4 more digits of real precision beyond
        // that — e.g. 0.000000006894 has 8 leading zeros, so this shows
        // 12 decimal places, landing exactly on "6894" and nothing more.
        Math.min(20, Math.max(0, -Math.floor(Math.log10(abs)) - 1) + 4);
  const minimumFractionDigits = maximumFractionDigits <= 2 ? maximumFractionDigits : 0;
  return applyCurrencyGlyphOverrides(
    createCurrencyFormatter(currency, maximumFractionDigits, minimumFractionDigits).format(value),
    currency,
  );
}

export function formatSignedCurrency(amount: number | string, currency: string = getCurrency()): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatCurrency(value, currency)}`;
}

/** "Hide balance" masking — wraps an already-formatted amount (currency,
 * quantity, whatever reveals a dollar figure) rather than reformatting it,
 * so call sites don't need a separate hidden-vs-shown branch for every
 * number. Percentages are deliberately never masked by callers — a % move
 * doesn't reveal how much money is actually involved. */
export function maskAmount(formatted: string, hidden: boolean): string {
  return hidden ? "••••" : formatted;
}

/** Strips trailing zeros from a decimal string for pre-filling an editable
 * number input — the backend stores crypto quantity/price as Numeric(38,18)
 * and returns it at full scale (e.g. "3.000000000000000000"), which is
 * correct for computation but not something anyone wants to see or edit
 * around in a form field. Works on the string directly rather than via
 * Number(), which would round a genuine 18-decimal-place amount (a
 * wei-level token quantity) through floating point instead of just
 * trimming the padding. */
export function trimTrailingZeros(value: string): string {
  if (!value.includes(".")) return value;
  const trimmed = value.replace(/0+$/, "").replace(/\.$/, "");
  return trimmed === "" || trimmed === "-" || trimmed === "-0" ? "0" : trimmed;
}

const MONTH_LABELS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] as const;
const MONTH_LABELS_RU = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"] as const;

export function getMonthLabels(language: Language): readonly string[] {
  return language === "ru" ? MONTH_LABELS_RU : MONTH_LABELS_EN;
}

/** `includeYear` is for contexts spanning multiple years (e.g. an all-time
 * search) where "Aug 16" alone wouldn't say which year. */
export function formatTransactionDate(isoDate: string, includeYear = false): string {
  const date = new Date(`${isoDate}T00:00:00`);
  return new Intl.DateTimeFormat(getIntlLocale(), {
    month: "short",
    day: "numeric",
    year: includeYear ? "numeric" : undefined,
  }).format(date);
}

/** Russian noun pluralization: pick the right form for 1/2-4/5+ (with the
 * 11-14 exception), e.g. pluralizeRu(3, "актив", "актива", "активов"). */
export function pluralizeRu(count: number, one: string, few: string, many: string): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
