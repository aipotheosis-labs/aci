// src/components/context/project-context.tsx
"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { Project } from "@/lib/types/project";
import { useProjects } from "@/hooks/use-project";
import { useOrgInfo } from "./org-context";
import { useAuthInfo } from "@propelauth/react";
import { LoadingGuard } from "./loading-guard";

type ProjectCtx = {
  projects: Project[];
  activeProject: Project | null;
  setActiveProject: (p: Project) => void;
  reloadActiveProject: () => Promise<void>;
};

const ProjectContext = createContext<ProjectCtx | null>(null);
export const useProjectInfo = () => {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProjectInfo must be within ProjectProvider");
  return ctx;
};

export const ProjectProvider = ({ children }: { children: ReactNode }) => {
  const { activeOrg } = useOrgInfo();
  const { accessToken } = useAuthInfo();

  const safeAccessToken = accessToken || undefined;

  const {
    data: projects = [],
    refetch,
    isFetching,
  } = useProjects(activeOrg?.orgId, safeAccessToken);

  const [activeProject, setActiveProject] = useState<Project | null>(null);

  useEffect(() => {
    if (!activeOrg || !projects.length) return;
    const key = `activeProject_${activeOrg.orgId}`;
    const saved = localStorage.getItem(key);
    setActiveProject(projects.find((p) => p.id === saved) ?? projects[0]);
  }, [projects, activeOrg]);

  useEffect(() => {
    if (activeOrg && activeProject) {
      localStorage.setItem(
        `activeProject_${activeOrg.orgId}`,
        activeProject.id,
      );
    }
  }, [activeProject, activeOrg]);

  const reloadActiveProject = useCallback(async () => {
    await refetch();
  }, [refetch]);

  return (
    <LoadingGuard
      isLoading={!activeOrg || !accessToken || isFetching || !activeProject}
    >
      <ProjectContext.Provider
        value={{
          projects,
          activeProject,
          setActiveProject,
          reloadActiveProject,
        }}
      >
        {children}
      </ProjectContext.Provider>
    </LoadingGuard>
  );
};
