import { Plan } from "@/lib/types/billing";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RiUserSettingsLine } from "react-icons/ri";
import { SettingsItem } from "./settings-item";
import { UpgradeButton } from "@/components/layout/subscription-button";
import { BsStars } from "react-icons/bs";
import Link from "next/link";

interface SubscriptionDisplayProps {
  subscription:
    | {
        plan: Plan;
      }
    | undefined;
  isLoading: boolean;
  onManageSubscription: () => void;
}

export function SubscriptionDisplay({
  subscription,
  isLoading,
  onManageSubscription,
}: SubscriptionDisplayProps) {
  return (
    <SettingsItem
      icon={BsStars}
      label="Subscription"
      description={
        isLoading ? (
          <div className="space-y-2 mt-1">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        ) : subscription ? (
          <div className="mt-1">
            <div className="flex items-center justify-between">
              <UpgradeButton size="sm" />
              {subscription.plan !== Plan.Free && (
                <Button
                  variant="default"
                  className="gap-2 ml-2"
                  onClick={onManageSubscription}
                >
                  <RiUserSettingsLine className="h-4 w-4" />
                  Manage Subscription
                </Button>
              )}
            </div>
            {subscription.plan !== Plan.Free && (
              <p className="text-sm text-muted-foreground mt-2">
                Need help with your subscription?{" "}
                <Link
                  href="mailto:support@aipolabs.xyz"
                  className="text-primary hover:underline"
                >
                  Contact support
                </Link>
              </p>
            )}
          </div>
        ) : null
      }
    />
  );
}
