// src/components/context/org-context.tsx
"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { OrgMemberInfoClass, useAuthInfo } from "@propelauth/react";
import { useQuery } from "@tanstack/react-query";
import { UserClass } from "@propelauth/javascript";
import { LoadingGuard } from "./loading-guard";

type OrgCtx = {
  orgs: OrgMemberInfoClass[];
  activeOrg: OrgMemberInfoClass | null;
  setActiveOrg: (o: OrgMemberInfoClass) => void;
  reloadOrgs: () => Promise<void>;
};

const OrgContext = createContext<OrgCtx | null>(null);
export const useOrgInfo = () => {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error("useOrgInfo must be within OrgProvider");
  return ctx;
};

const fetchOrgs = async (
  userClass: UserClass,
  refreshAuthInfo: () => Promise<void>,
) => {
  let orgs = userClass?.getOrgs?.() ?? [];
  let retry = 0;
  while (!orgs.length && retry < 5) {
    await refreshAuthInfo();
    await new Promise((r) => setTimeout(r, 800));
    orgs = userClass.getOrgs();
    retry++;
  }
  return orgs as OrgMemberInfoClass[];
};

export const OrgProvider = ({ children }: { children: ReactNode }) => {
  const { userClass, refreshAuthInfo } = useAuthInfo();

  const {
    data: orgs = [],
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["orgs", userClass?.userId],
    queryFn: () => fetchOrgs(userClass!, refreshAuthInfo),
    enabled: !!userClass,
    staleTime: 30 * 60_000,
    initialData: () => {
      const cache = localStorage.getItem("orgs_cache");
      if (cache) {
        try {
          return JSON.parse(cache) as OrgMemberInfoClass[];
        } catch {
          return [];
        }
      }
      return [];
    },
  });

  const [activeOrg, setActiveOrg] = useState<OrgMemberInfoClass | null>(null);

  useEffect(() => {
    if (orgs.length > 0) {
      localStorage.setItem("orgs_cache", JSON.stringify(orgs));
    }
  }, [orgs]);

  useEffect(() => {
    if (!orgs.length) return;
    const saved = localStorage.getItem("activeOrgId");
    setActiveOrg(orgs.find((o) => o.orgId === saved) ?? orgs[0]);
  }, [orgs]);

  useEffect(() => {
    if (activeOrg) localStorage.setItem("activeOrgId", activeOrg.orgId);
  }, [activeOrg]);

  const reloadOrgs = useCallback(async () => {
    await refetch();
  }, [refetch]);

  return (
    <LoadingGuard isLoading={isLoading || !activeOrg}>
      <OrgContext.Provider
        value={{ orgs, activeOrg, setActiveOrg, reloadOrgs }}
      >
        {children}
      </OrgContext.Provider>
    </LoadingGuard>
  );
};
