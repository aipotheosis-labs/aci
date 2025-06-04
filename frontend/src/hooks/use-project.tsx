"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
} from "@/lib/api/project";
import { Project } from "@/lib/types/project";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";
export const projectKeys = {
  all: (orgId: string) => ["projects", orgId] as const,
  detail: (orgId: string, projectId: string) =>
    ["projects", orgId, projectId] as const,
};

export const useProjects = (orgId?: string, accessToken?: string) => {
  return useQuery<Project[], Error>({
    queryKey: orgId ? projectKeys.all(orgId) : ["projects"],
    queryFn: async () => {
      const fetchedProjects = await getProjects(accessToken!, orgId!);

      return [...fetchedProjects].sort((a, b) => {
        return (
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
      });
    },
    enabled: !!orgId && !!accessToken,
    retry: 2,
    retryDelay: 1000,
  });
};

export const useProject = (projectId?: string) => {
  const { activeOrg, accessToken } = useMetaInfo();
  const { data: projects } = useProjects(activeOrg.orgId, accessToken);

  return {
    project: projectId ? projects?.find((p) => p.id === projectId) : undefined,
    projects,
  };
};

type CreateProjectParams = {
  name: string;
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  const { activeOrg, accessToken } = useMetaInfo();
  return useMutation<Project, Error, CreateProjectParams>({
    mutationFn: (params) =>
      createProject(accessToken, params.name, activeOrg.orgId),
    onSuccess: (newProject) => {
      queryClient.setQueryData<Project[]>(
        projectKeys.all(activeOrg.orgId),
        (old = []) => [...old, newProject],
      );
      queryClient.invalidateQueries({
        queryKey: projectKeys.all(activeOrg.orgId),
      });
      toast.success("project created successfully");
    },
    onError: (error) => {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("create project failed");
      }
    },
  });
};

type UpdateProjectParams = {
  name: string;
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();
  const { activeProject, accessToken, activeOrg } = useMetaInfo();

  return useMutation<Project, Error, UpdateProjectParams>({
    mutationFn: (params) =>
      updateProject(accessToken, activeProject.id, params.name),
    onSuccess: (updatedProject) => {
      queryClient.setQueryData<Project[]>(
        projectKeys.all(activeOrg.orgId),
        (old = []) =>
          old.map((project) =>
            project.id === activeProject.id ? updatedProject : project,
          ),
      );
      queryClient.invalidateQueries({
        queryKey: projectKeys.all(activeOrg.orgId),
      });
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(activeOrg.orgId, activeProject.id),
      });
      toast.success("project updated successfully");
    },
    onError: (error) => {
      console.error("update project failed:", error);
      toast.error("update project failed");
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  const { activeProject, accessToken, activeOrg } = useMetaInfo();
  return useMutation<void, Error>({
    mutationFn: () => deleteProject(accessToken, activeProject.id),
    onSuccess: () => {
      queryClient.setQueryData<Project[]>(
        projectKeys.all(activeOrg.orgId),
        (old = []) => old.filter((project) => project.id !== activeProject.id),
      );
      queryClient.invalidateQueries({
        queryKey: projectKeys.all(activeOrg.orgId),
      });
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(activeOrg.orgId, activeProject.id),
      });
      toast.success("project deleted successfully");
    },
    onError: (error) => {
      console.error("delete project failed:", error);
      toast.error("delete project failed");
    },
  });
};

// provide a method to reload projects
export const useReloadProjects = () => {
  const queryClient = useQueryClient();

  return useCallback(
    async (orgId: string) => {
      if (orgId) {
        await queryClient.invalidateQueries({
          queryKey: projectKeys.all(orgId),
        });
      }
    },
    [queryClient],
  );
};
