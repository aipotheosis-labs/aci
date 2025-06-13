"use client";

import { useAuthInfo } from "@propelauth/react";
import { useOrgInfo } from "./org-context";
import { useProjectInfo } from "./project-context";
import { OrgMemberInfoClass } from "@propelauth/react";
import { Project } from "@/lib/types/project";

export const useMetaInfo = () => {
  const { userClass, accessToken } = useAuthInfo();
  const { orgs, activeOrg, setActiveOrg } = useOrgInfo();
  const { projects, activeProject, setActiveProject, reloadActiveProject } =
    useProjectInfo();
  if (!accessToken || !activeOrg || !activeProject || !userClass) {
    throw new Error(
      "useMetaInfo: Context not ready - ensure you're using it within the proper providers",
    );
  }

  return {
    user: userClass,
    orgs,
    activeOrg: activeOrg as OrgMemberInfoClass,
    setActiveOrg,
    projects,
    activeProject: activeProject as Project,
    setActiveProject,
    reloadActiveProject,
    accessToken: accessToken as string,
  };
};
