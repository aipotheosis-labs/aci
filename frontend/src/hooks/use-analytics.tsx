"use client";

import { useQueries, UseQueryResult } from "@tanstack/react-query";
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
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

export const analyticsKeys = {
  // Since it is not a data source of an interface, in order to unify the usage of all APIs, use base
  base: (projectId: string) => ["analytics", projectId] as const,
  appDistribution: (projectId: string) =>
    [...analyticsKeys.base(projectId), "app-distribution"] as const,
  functionDistribution: (projectId: string) =>
    [...analyticsKeys.base(projectId), "function-distribution"] as const,
  appTimeSeries: (projectId: string) =>
    [...analyticsKeys.base(projectId), "app-time-series"] as const,
  functionTimeSeries: (projectId: string) =>
    [...analyticsKeys.base(projectId), "function-time-series"] as const,
};

export function useAnalyticsQueries() {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  const results = useQueries({
    queries: [
      {
        queryKey: analyticsKeys.appDistribution(activeProject.id),
        queryFn: () => getAppDistributionData(apiKey),
        enabled: !!activeProject && !!apiKey,
        staleTime: 0,
      },
      {
        queryKey: analyticsKeys.functionDistribution(activeProject.id),
        queryFn: () => getFunctionDistributionData(apiKey),
        enabled: !!activeProject && !!apiKey,
        staleTime: 0,
      },
      {
        queryKey: analyticsKeys.appTimeSeries(activeProject.id),
        queryFn: () => getAppTimeSeriesData(apiKey),
        enabled: !!activeProject && !!apiKey,
        staleTime: 0,
      },
      {
        queryKey: analyticsKeys.functionTimeSeries(activeProject.id),
        queryFn: () => getFunctionTimeSeriesData(apiKey),
        enabled: !!activeProject && !!apiKey,
        staleTime: 0,
      },
    ],
  });

  const [
    appDistributionQuery,
    functionDistributionQuery,
    appTimeSeriesQuery,
    functionTimeSeriesQuery,
  ] = results as [
    UseQueryResult<DistributionDatapoint[], Error>,
    UseQueryResult<DistributionDatapoint[], Error>,
    UseQueryResult<TimeSeriesDatapoint[], Error>,
    UseQueryResult<TimeSeriesDatapoint[], Error>,
  ];

  return {
    appDistributionData: appDistributionQuery.data ?? [],
    functionDistributionData: functionDistributionQuery.data ?? [],
    appTimeSeriesData: appTimeSeriesQuery.data ?? [],
    functionTimeSeriesData: functionTimeSeriesQuery.data ?? [],
    isLoading: results.some((query) => query.isLoading),
    error: results.find((query) => query.error)?.error || null,
    refetchAll: () => Promise.all(results.map((query) => query.refetch())),
  };
}
