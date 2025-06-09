"use client";

import { useQuery } from "@tanstack/react-query";
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

export function useAppDistribution() {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<DistributionDatapoint[], Error>({
    queryKey: analyticsKeys.appDistribution(activeProject.id),
    queryFn: () => getAppDistributionData(apiKey),
    enabled: !!activeProject && !!apiKey,
  });
}

export function useFunctionDistribution() {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<DistributionDatapoint[], Error>({
    queryKey: analyticsKeys.functionDistribution(activeProject.id),
    queryFn: () => getFunctionDistributionData(apiKey),
    enabled: !!activeProject && !!apiKey,
  });
}

export function useAppTimeSeries() {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<TimeSeriesDatapoint[], Error>({
    queryKey: analyticsKeys.appTimeSeries(activeProject.id),
    queryFn: () => getAppTimeSeriesData(apiKey),
    enabled: !!activeProject && !!apiKey,
  });
}

export function useFunctionTimeSeries() {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<TimeSeriesDatapoint[], Error>({
    queryKey: analyticsKeys.functionTimeSeries(activeProject.id),
    queryFn: () => getFunctionTimeSeriesData(apiKey),
    enabled: !!activeProject && !!apiKey,
  });
}
