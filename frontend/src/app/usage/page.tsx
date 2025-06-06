"use client";

import { useEffect, useState } from "react";
import UsagePieChart from "@/components/charts/usage-pie-chart";
import { UsageBarChart } from "@/components/charts/usage-bar-chart";
import { QuotaUsageDisplay } from "@/components/quota/quota-usage-display";
import { Separator } from "@/components/ui/separator";
import {
  getAppDistributionData,
  getFunctionDistributionData,
  getAppTimeSeriesData,
  getFunctionTimeSeriesData,
} from "@/lib/api/analytics";
import {
  DistributionDatapoint,
  TimeSeriesDatapoint,
} from "@/lib/types/analytics";
import { getApiKey } from "@/lib/api/util";
import { useMetaInfo } from "@/components/context/metainfo";
import { useQuota } from "@/hooks/use-quota";

export default function UsagePage() {
  const { activeProject } = useMetaInfo();
  const [appDistributionData, setAppDistributionData] = useState<
    DistributionDatapoint[]
  >([]);
  const [functionDistributionData, setFunctionDistributionData] = useState<
    DistributionDatapoint[]
  >([]);
  const [appTimeSeriesData, setAppTimeSeriesData] = useState<
    TimeSeriesDatapoint[]
  >([]);
  const [functionTimeSeriesData, setFunctionTimeSeriesData] = useState<
    TimeSeriesDatapoint[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { data: quotaUsage } = useQuota();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const apiKey = getApiKey(activeProject);

        const [appDistData, funcDistData, appTimeData, funcTimeData] =
          await Promise.all([
            getAppDistributionData(apiKey),
            getFunctionDistributionData(apiKey),
            getAppTimeSeriesData(apiKey),
            getFunctionTimeSeriesData(apiKey),
          ]);

        setAppDistributionData(appDistData);
        setFunctionDistributionData(funcDistData);
        setAppTimeSeriesData(appTimeData);
        setFunctionTimeSeriesData(funcTimeData);
      } catch (err) {
        console.error("Error fetching analytics data:", err);
        setError("Failed to load analytics data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [activeProject]);

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
        {error ? (
          <div className="p-4 text-red-500">{error}</div>
        ) : isLoading ? (
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
