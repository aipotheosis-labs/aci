"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getAllAppConfigs,
  createAppConfig,
  updateAppConfig,
  deleteAppConfig,
  getAppConfig,
} from "@/lib/api/appconfig";
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
import { AppConfig } from "@/lib/types/appconfig";
import { toast } from "sonner";

// TODO: think about what happens when the active project changes, and how to invalidate
// the cache. May need to add project id to the query key.
export const appConfigKeys = {
  all: ["appconfigs"] as const,
  detail: (appName: string | null | undefined) =>
    ["appconfigs", appName ?? ""] as const,
};

export const useAppConfigs = () => {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<AppConfig[], Error>({
    queryKey: appConfigKeys.all,
    queryFn: () => getAllAppConfigs(apiKey),
  });
};

export const useAppConfig = (appName?: string | null) => {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<AppConfig | null, Error>({
    queryKey: appConfigKeys.detail(appName),
    queryFn: () =>
      appName ? getAppConfig(appName, apiKey) : Promise.resolve(null),
    enabled: !!appName,
  });
};

type CreateAppConfigParams = {
  app_name: string;
  security_scheme: string;
  security_scheme_overrides?: {
    oauth2?: {
      client_id: string;
      client_secret: string;
    } | null;
  };
};

export const useCreateAppConfig = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<AppConfig, Error, CreateAppConfigParams>({
    mutationFn: (params) =>
      createAppConfig(
        params.app_name,
        params.security_scheme,
        apiKey,
        params.security_scheme_overrides,
      ),
    onSuccess: (newConfig) => {
      queryClient.setQueryData<AppConfig[]>(appConfigKeys.all, (old = []) => [
        ...old,
        newConfig,
      ]);
      queryClient.invalidateQueries({ queryKey: appConfigKeys.all });
    },
    onError: (error) => {
      console.error("Create AppConfig failed:", error);
      toast.error("Failed to create app configuration");
    },
  });
};

type UpdateAppConfigParams = {
  app_name: string;
  enabled: boolean;
};

export const useUpdateAppConfig = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<AppConfig, Error, UpdateAppConfigParams>({
    mutationFn: (params) =>
      updateAppConfig(params.app_name, params.enabled, apiKey),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: appConfigKeys.all });
      // The current page may only use the update of a single data item when updating
      queryClient.invalidateQueries({
        queryKey: appConfigKeys.detail(variables.app_name),
      });
    },
    onError: (error) => {
      console.error("Update AppConfig failed:", error);
      toast.error("Failed to update app configuration");
    },
  });
};

export const useDeleteAppConfig = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<Response, Error, string>({
    mutationFn: (app_name) => deleteAppConfig(app_name, apiKey),
    onSuccess: (_, app_name) => {
      queryClient.invalidateQueries({ queryKey: appConfigKeys.all });
      queryClient.invalidateQueries({
        queryKey: appConfigKeys.detail(app_name),
      });
    },
    onError: (error) => {
      console.error("Delete AppConfig failed:", error);
      toast.error("Failed to delete app configuration");
    },
  });
};
