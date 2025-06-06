import { useMetaInfo } from "@/components/context/metainfo";
import { getQuotaUsage } from "@/lib/api/quota";
import { useQuery } from "@tanstack/react-query";

export const quotaKeys = {
  all: ["quota"] as const,
};

export function useQuota() {
  const { accessToken, activeOrg } = useMetaInfo();

  return useQuery({
    queryKey: quotaKeys.all,
    queryFn: () => getQuotaUsage(accessToken, activeOrg.orgId),
    enabled: !!activeOrg.orgId && !!accessToken,
    refetchInterval: 1000 * 30,
    staleTime: 0,
  });
}
