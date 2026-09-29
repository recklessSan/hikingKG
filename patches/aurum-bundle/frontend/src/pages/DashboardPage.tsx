import { useMemo, useState } from "react";
import { MonthSelector } from "@/components/layout/MonthSelector";
import { YearSelector } from "@/components/layout/YearSelector";
import { StatCard } from "@/components/dashboard/StatCard";
import { SpendingByCategoryCard } from "@/components/dashboard/SpendingByCategoryCard";
import { RecentTransactionsCard } from "@/components/dashboard/RecentTransactionsCard";
import { AlertBanner } from "@/components/insights/AlertBanner";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { useTransactionYears } from "@/hooks/useTransactions";
import { getCurrencyLabel } from "@/lib/currency";
import { formatCurrency, formatSignedCurrency, getCurrencySymbol } from "@/lib/format";
import { useTranslation } from "@/lib/i18n";
import type { CurrencyDashboardSummary } from "@/types";

/** Share of income left over after spending (net / real_income). `null` when
 * there was no income to take a share of, rather than a misleading 0%. */
function savingsRate(realIncome: number, net: number): number | null {
  return realIncome > 0 ? (net / realIncome) * 100 : null;
}

function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(0)}%`;
}

function CurrencyStatsBlock({
  slice,
  showHeading,
}: {
  slice: CurrencyDashboardSummary;
  showHeading: boolean;
}) {
  const { t, language } = useTranslation();
  const rate = savingsRate(Number(slice.real_income), Number(slice.net));
  const symbol = getCurrencySymbol(slice.currency);
  const heading =
    symbol !== slice.currency
      ? `${getCurrencyLabel(slice.currency, language)} (${symbol})`
      : getCurrencyLabel(slice.currency, language);

  return (
    <section className="space-y-3">
      {showHeading && (
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-secondary">{heading}</h2>
      )}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <StatCard
          label={t("dashboard.statRealIncomeLabel")}
          value={formatCurrency(slice.real_income, slice.currency)}
          caption={t("dashboard.statRealIncomeCaption")}
          tone="success"
        />
        <StatCard
          label={t("dashboard.statSpentLabel")}
          value={formatCurrency(slice.spent, slice.currency)}
          caption={t("dashboard.statSpentCaption")}
          tone="danger"
        />
        <StatCard
          label={t("dashboard.statNetLabel")}
          value={formatSignedCurrency(slice.net, slice.currency)}
          caption={t("dashboard.statNetCaption")}
          tone={Number(slice.net) >= 0 ? "success" : "danger"}
        />
        <StatCard
          label={t("dashboard.statSavingsRateLabel")}
          value={rate === null ? "—" : formatPercent(rate)}
          caption={t("dashboard.statSavingsRateCaption")}
          tone={rate === null ? "default" : rate >= 0 ? "success" : "danger"}
        />
      </div>
      <SpendingByCategoryCard
        items={slice.spending_by_category}
        currency={slice.currency}
        title={
          showHeading
            ? t("dashboard.spendingByCategoryTitleCurrency", { currency: slice.currency })
            : undefined
        }
      />
    </section>
  );
}

export function DashboardPage() {
  const { t, currency: appCurrency } = useTranslation();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const { data: years } = useTransactionYears();

  const { data, isLoading, isError } = useDashboardSummary(year, month);

  const slices = useMemo(() => {
    const byCurrency = data?.by_currency ?? [];
    if (byCurrency.length > 0) {
      // App primary currency first, then the rest A→Z (API already sorts A→Z).
      return [...byCurrency].sort((a, b) => {
        if (a.currency === appCurrency) return -1;
        if (b.currency === appCurrency) return 1;
        return a.currency.localeCompare(b.currency);
      });
    }
    // Older backends without by_currency — single synthetic slice.
    if (!data) return [];
    return [
      {
        currency: appCurrency,
        real_income: data.real_income,
        spent: data.spent,
        net: data.net,
        transferred_out: data.transferred_out,
        spending_by_category: data.spending_by_category,
      },
    ];
  }, [data, appCurrency]);

  const multiCurrency = slices.length > 1;

  return (
    <div className="space-y-5">
      <AlertBanner excludeKeys={["risky_allocation_exceeded"]} />

      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <MonthSelector month={month} onChange={setMonth} />
        </div>
        <YearSelector years={years ?? [now.getFullYear()]} year={year} onChange={setYear} />
      </div>

      {isError && (
        <p className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {t("dashboard.errorLoading")}
        </p>
      )}

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          <StatCard label={t("dashboard.statRealIncomeLabel")} value="…" caption={t("dashboard.statRealIncomeCaption")} />
          <StatCard label={t("dashboard.statSpentLabel")} value="…" caption={t("dashboard.statSpentCaption")} />
          <StatCard label={t("dashboard.statNetLabel")} value="…" caption={t("dashboard.statNetCaption")} />
          <StatCard label={t("dashboard.statSavingsRateLabel")} value="…" caption={t("dashboard.statSavingsRateCaption")} />
        </div>
      ) : (
        <div className="space-y-8">
          {multiCurrency && (
            <p className="text-xs text-text-muted">{t("dashboard.multiCurrencyHint")}</p>
          )}
          {slices.map((slice) => (
            <CurrencyStatsBlock key={slice.currency} slice={slice} showHeading={multiCurrency} />
          ))}
          {slices.length === 0 && !isError && (
            <p className="py-6 text-center text-sm text-text-muted">{t("dashboard.noActivityThisMonth")}</p>
          )}
        </div>
      )}

      <RecentTransactionsCard year={year} month={month} />
    </div>
  );
}
