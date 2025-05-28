"use client";

import { useMutation } from "@tanstack/react-query";
import { useMetaInfo } from "@/components/context/metainfo";
import { toast } from "sonner";
import { createAgent, updateAgent, deleteAgent } from "@/lib/api/agent";
import { Agent } from "@/lib/types/project";

type CreateAgentParams = {
  name: string;
  description: string;
  allowed_apps?: string[];
  custom_instructions?: Record<string, string>;
};

export const useCreateAgent = () => {
  const { activeProject, accessToken, reloadActiveProject } = useMetaInfo();

  return useMutation<Agent, Error, CreateAgentParams>({
    mutationFn: (params) =>
      createAgent(
        activeProject.id,
        accessToken,
        params.name,
        params.description,
        params.allowed_apps,
        params.custom_instructions,
      ),
    onSuccess: () => {
      reloadActiveProject();
    },
    onError: () => toast.error("Failed to create agent"),
  });
};

type UpdateAgentParams = {
  id: string;
  data: Partial<Omit<CreateAgentParams, "name" | "description">> & {
    name?: string;
    description?: string;
  };
  noreload?: boolean;
};

export const useUpdateAgent = () => {
  const { activeProject, accessToken, reloadActiveProject } = useMetaInfo();

  return useMutation<Agent, Error, UpdateAgentParams>({
    mutationFn: ({ id, data }) =>
      updateAgent(
        activeProject.id,
        id,
        accessToken,
        data.name,
        data.description,
        data.allowed_apps,
        data.custom_instructions,
      ),
    onSuccess: (_, { noreload }) => {
      if (!noreload) reloadActiveProject();
    },
  });
};

// delete Agent
export const useDeleteAgent = () => {
  const { activeProject, accessToken, reloadActiveProject } = useMetaInfo();

  return useMutation<void, Error, string>({
    mutationFn: (agentId) =>
      deleteAgent(activeProject.id, agentId, accessToken),
    onSuccess: () => {
      reloadActiveProject();
      toast.success("Agent deleted successfully");
    },
    onError: () => toast.error("Failed to delete agent"),
  });
};
