"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMetaInfo } from "@/components/context/metainfo";
import { createAgent, updateAgent, deleteAgent } from "@/lib/api/agent";
import { getProjects } from "@/lib/api/project";
import { Agent } from "@/lib/types/project";

// get all Agents No scene found, only need to get the scene of being an agent
export const useAgents = () => {
  const { activeProject, accessToken, activeOrg } = useMetaInfo();

  return useQuery<Agent[], Error>({
    queryKey: ["agents", activeProject.id],
    queryFn: async () => {
      const projects = await getProjects(accessToken, activeOrg.orgId);
      const project = projects.find((p) => p.id === activeProject.id);
      return project?.agents || [];
    },
  });
};

type CreateAgentParams = {
  name: string;
  description: string;
  allowed_apps?: string[];
  custom_instructions?: Record<string, string>;
};

// create Agent
export const useCreateAgent = () => {
  const queryClient = useQueryClient();
  const { activeProject, accessToken } = useMetaInfo();

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
    onSuccess: (newAgent) => {
      queryClient.setQueryData<Agent[]>(
        ["agents", activeProject.id],
        (old = []) => [...old, newAgent],
      );
      queryClient.invalidateQueries({ queryKey: ["agents", activeProject.id] });
    },
  });
};

type UpdateAgentParams = {
  id: string;
  data: {
    name?: string;
    description?: string;
    allowed_apps?: string[];
    custom_instructions?: Record<string, string>;
  };
};

// update Agent
export const useUpdateAgent = () => {
  const queryClient = useQueryClient();
  const { activeProject, accessToken } = useMetaInfo();

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
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["agents", activeProject.id] });
      queryClient.invalidateQueries({
        queryKey: ["agents", activeProject.id, id],
      });
    },
  });
};

// delete Agent
export const useDeleteAgent = () => {
  const queryClient = useQueryClient();
  const { activeProject, accessToken } = useMetaInfo();

  return useMutation<void, Error, string>({
    mutationFn: (agentId) =>
      deleteAgent(activeProject.id, agentId, accessToken),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["agents", activeProject.id] });
      queryClient.invalidateQueries({
        queryKey: ["agents", activeProject.id, id],
      });
    },
  });
};
