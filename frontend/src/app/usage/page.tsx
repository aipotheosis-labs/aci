"use client";

import UsagePieChart from "@/components/charts/usage-pie-chart";
import { UsageBarChart } from "@/components/charts/usage-bar-chart";
import { QuotaUsageDisplay } from "@/components/quota/quota-usage-display";
import { Separator } from "@/components/ui/separator";
import { useQuota } from "@/hooks/use-quota";
import { useAnalyticsQueries } from "@/hooks/use-analytics";

export default function UsagePage() {
  const {
    data: quotaUsage,
    isLoading: isQuotaLoading,
    error: quotaError,
  } = useQuota();

  const {
    appDistributionData,
    functionDistributionData,
    appTimeSeriesData,
    functionTimeSeriesData,
    isLoading: isAnalyticsLoading,
    error: AnalyticsError,
  } = useAnalyticsQueries();

  const isInitialLoading = isQuotaLoading || isAnalyticsLoading;

  const hasError = quotaError || AnalyticsError;

  const errorMessage = hasError
    ? "Failed to load analytics data. Please try again later."
    : null;

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Usage</h1>
        <div className="flex items-center gap-4">
          {/* <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              Analytics View
            </span>
          </div> */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              From the last 7 days
            </span>
          </div>
          {/* <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Monthly</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Filter</span>
          </div> */}
        </div>
      </div>

      <Separator />

      <div className="flex flex-col gap-6 p-6">
        {errorMessage ? (
          <div className="p-4 text-red-500">{errorMessage}</div>
        ) : isInitialLoading ? (
          <div className="p-4">Loading analytics data...</div>
        ) : (
          <>
            {/* quota usage */}
            {quotaUsage && (
              <div className="w-full">
                <QuotaUsageDisplay quotaUsage={quotaUsage} />
              </div>
            )}

            <div className="grid gap-6 grid-cols-12">
              <div className="col-span-8">
                <UsageBarChart title="App Usage" data={appTimeSeriesData} />
              </div>
              <div className="col-span-4">
                <UsagePieChart
                  title="App Usage Distribution"
                  data={appDistributionData}
                  cutoff={6}
                />
              </div>

              <div className="col-span-8">
                <UsageBarChart
                  title="Function Usage"
                  data={functionTimeSeriesData}
                />
              </div>
              <div className="col-span-4">
                <UsagePieChart
                  title="Function Usage Distribution"
                  data={functionDistributionData}
                  cutoff={6}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
