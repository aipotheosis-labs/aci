"use client";

import { getProjects } from "@/lib/api/project";
import { Project } from "@/lib/types/project";
import {
  OrgMemberInfoClass,
  WithLoggedInAuthInfoProps,
  withRequiredAuthInfo,
} from "@propelauth/react";
import {
  createContext,
  ReactNode,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { UserClass } from "@propelauth/javascript";
import { useQuery, useQueryClient } from "@tanstack/react-query";

export const metaKeys = {
  projects: (orgId: string) => ["projects", orgId] as const,
};

interface MetaInfoContextType {
  user: UserClass;
  orgs: OrgMemberInfoClass[];
  activeOrg: OrgMemberInfoClass;
  setActiveOrg: (org: OrgMemberInfoClass) => void;
  projects: Project[];
  activeProject: Project;
  reloadActiveProject: () => Promise<void>;
  setActiveProject: (project: Project) => void;
  accessToken: string;
}

const MetaInfoContext = createContext<MetaInfoContextType | undefined>(
  undefined,
);

interface MetaInfoProviderProps extends WithLoggedInAuthInfoProps {
  children: ReactNode;
}

export const MetaInfoProvider = withRequiredAuthInfo<MetaInfoProviderProps>(
  ({ children, userClass, accessToken, refreshAuthInfo }) => {
    const [orgs, setOrgs] = useState<OrgMemberInfoClass[]>([]);
    const [activeOrg, setActiveOrg] = useState<OrgMemberInfoClass | null>(null);
    const queryClient = useQueryClient();
    const [activeProject, setActiveProject] = useState<Project | null>(null);

    useEffect(() => {
      async function getOrgs() {
        // TODO: refactor this retry logic to use TanStack Query to
        // elegantly handle the loading and error state
        let retrievedOrgs = userClass.getOrgs();

        let attempts = 0;
        const maxAttempts = 5;

        // Wait for the default Personal Org to be created
        while (retrievedOrgs.length === 0 && attempts < maxAttempts) {
          await refreshAuthInfo();
          await new Promise((resolve) => setTimeout(resolve, 1000));
          retrievedOrgs = userClass.getOrgs();
          attempts++;
          console.log("retrievedOrgs", retrievedOrgs, attempts);
        }
        setOrgs(retrievedOrgs);
      }
      getOrgs();
    }, [userClass, refreshAuthInfo]);

    useEffect(() => {
      if (orgs.length > 0) {
        // TODO: get active org from local storage
        setActiveOrg(orgs[0]);
      }
    }, [orgs]);

    const { data: projects = [] } = useQuery<Project[], Error>({
      queryKey:
        activeOrg && accessToken
          ? metaKeys.projects(activeOrg.orgId)
          : ["projects"],
      queryFn: () => getProjects(accessToken, activeOrg!.orgId),
      enabled: !!activeOrg && !!accessToken,
      retry: 2,
      retryDelay: 1000,
    });

    useEffect(() => {
      if (projects.length > 0) {
        // TODO: get active project from local storage
        setActiveProject(projects[0]);
      }
    }, [projects]);

    const reloadActiveProject = useCallback(async () => {
      if (activeOrg && accessToken) {
        await queryClient.invalidateQueries({
          queryKey: metaKeys.projects(activeOrg.orgId),
        });
      }
    }, [queryClient, activeOrg, accessToken]);

    return (
      <div>
        {activeOrg && activeProject && accessToken ? (
          <MetaInfoContext.Provider
            value={{
              user: userClass,
              orgs,
              activeOrg,
              setActiveOrg,
              projects,
              activeProject,
              setActiveProject,
              reloadActiveProject,
              accessToken,
            }}
          >
            {children}
          </MetaInfoContext.Provider>
        ) : (
          <div className="flex flex-col items-center justify-center min-h-screen space-y-3">
            <h1 className="text-2xl font-semibold">
              Setting up your workspace...
            </h1>
            <Skeleton className="h-[125px] w-[250px] rounded-xl" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
          </div>
        )}
      </div>
    );
  },
);

export const useMetaInfo = () => {
  const context = useContext(MetaInfoContext);
  if (!context) {
    throw new Error("useMetaInfo must be used within a MetaInfoProvider");
  }
  return context;
};
