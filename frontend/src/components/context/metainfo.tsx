"use client";

import { useAuthInfo } from "@propelauth/react";
import { useOrgInfo } from "./org-context";
import { useProjectInfo } from "./project-context";

export const useMetaInfo = () => {
  const { userClass, accessToken } = useAuthInfo();
  const { orgs, activeOrg, setActiveOrg } = useOrgInfo();
  const { projects, activeProject, setActiveProject, reloadActiveProject } =
    useProjectInfo();

  return {
    user: userClass!,
    orgs,
    activeOrg: activeOrg!,
    setActiveOrg,
    projects,
    activeProject: activeProject!,
    setActiveProject,
    reloadActiveProject,
    accessToken: accessToken!,
  };
};
