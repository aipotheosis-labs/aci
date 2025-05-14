"use client";

import { useQuery } from "@tanstack/react-query";
import { getSubscription } from "../lib/api/billing";
import { useMetaInfo } from "@/components/context/metainfo";

export const useSubscription = () => {
  const { accessToken, activeOrg } = useMetaInfo();

  return useQuery({
    queryKey: ["subscription", activeOrg.orgId],
    queryFn: () => getSubscription(accessToken, activeOrg.orgId),
  });
};
