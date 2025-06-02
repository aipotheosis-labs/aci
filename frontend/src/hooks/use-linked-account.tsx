"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import {
  getAllLinkedAccounts,
  createAPILinkedAccount,
  createNoAuthLinkedAccount,
  deleteLinkedAccount,
  updateLinkedAccount,
  getOauth2LinkURL,
} from "@/lib/api/linkedaccount";
import { useMetaInfo } from "@/components/context/metainfo";
import { getApiKey } from "@/lib/api/util";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import { toast } from "sonner";

export const linkedAccountKeys = {
  all: (projectId: string) => [projectId, "linkedaccounts"] as const,
};

export const useLinkedAccounts = () => {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useQuery<LinkedAccount[], Error>({
    queryKey: linkedAccountKeys.all(activeProject.id),
    queryFn: () => getAllLinkedAccounts(apiKey),
  });
};

export const useAppLinkedAccounts = (appName?: string | null) => {
  const base = useLinkedAccounts();
  return {
    ...base,
    data: useMemo(
      () =>
        appName && base.data
          ? base.data.filter((a) => a.app_name === appName)
          : [],
      [base.data, appName],
    ),
  };
};

type CreateAPILinkedAccountParams = {
  appName: string;
  linkedAccountOwnerId: string;
  linkedAPIKey: string;
};

export const useCreateAPILinkedAccount = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<LinkedAccount, Error, CreateAPILinkedAccountParams>({
    mutationFn: (params) =>
      createAPILinkedAccount(
        params.appName,
        params.linkedAccountOwnerId,
        params.linkedAPIKey,
        apiKey,
      ),

    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: linkedAccountKeys.all(activeProject.id),
      }),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};

type CreateNoAuthLinkedAccountParams = {
  appName: string;
  linkedAccountOwnerId: string;
};

export const useCreateNoAuthLinkedAccount = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<LinkedAccount, Error, CreateNoAuthLinkedAccountParams>({
    mutationFn: (params) =>
      createNoAuthLinkedAccount(
        params.appName,
        params.linkedAccountOwnerId,
        apiKey,
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: linkedAccountKeys.all(activeProject.id),
      }),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
type GetOauth2LinkURLParams = {
  appName: string;
  linkedAccountOwnerId: string;
  afterOAuth2LinkRedirectURL?: string;
};

export const useGetOauth2LinkURL = () => {
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<string, Error, GetOauth2LinkURLParams>({
    mutationFn: (params) =>
      getOauth2LinkURL(
        params.appName,
        params.linkedAccountOwnerId,
        apiKey,
        params.afterOAuth2LinkRedirectURL,
      ),
    onError: (error) => {
      toast.error(error.message);
    },
  });
};

type DeleteLinkedAccountParams = {
  linkedAccountId: string;
};

export const useDeleteLinkedAccount = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<void, Error, DeleteLinkedAccountParams>({
    mutationFn: (params) => deleteLinkedAccount(params.linkedAccountId, apiKey),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: linkedAccountKeys.all(activeProject.id),
      }),
  });
};

type UpdateLinkedAccountParams = {
  linkedAccountId: string;
  enabled: boolean;
};

export const useUpdateLinkedAccount = () => {
  const queryClient = useQueryClient();
  const { activeProject } = useMetaInfo();
  const apiKey = getApiKey(activeProject);

  return useMutation<LinkedAccount, Error, UpdateLinkedAccountParams>({
    mutationFn: (params) =>
      updateLinkedAccount(params.linkedAccountId, apiKey, params.enabled),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: linkedAccountKeys.all(activeProject.id),
      }),
  });
};
