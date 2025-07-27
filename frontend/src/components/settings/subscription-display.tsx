import { Plan } from "@/lib/types/billing";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RiUserSettingsLine } from "react-icons/ri";
import { SettingsItem } from "./settings-item";
import { UpgradeButton } from "@/components/layout/upgrade-button";
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
              <div>
                <p className="text-sm font-medium">
                  {subscription.plan.charAt(0).toUpperCase() +
                    subscription.plan.slice(1) +
                    " Plan"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {subscription.plan === Plan.Free
                    ? "Basic features for small teams"
                    : "Advanced features for growing organizations"}
                </p>
              </div>
              <UpgradeButton size="sm" />
              {subscription.plan !== Plan.Free && (
                <Button
                  variant="outline"
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
                <Link href="/support" className="text-primary hover:underline">
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
