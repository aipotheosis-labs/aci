import { Plan } from "@/lib/types/billing";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { BsStars } from "react-icons/bs";
import { RiUserSettingsLine } from "react-icons/ri";
import Link from "next/link";
import { SettingsItem } from "./settings-item";

interface SubscriptionDisplayProps {
  subscription:
    | {
        plan: Plan;
      }
    | undefined;
  isLoading: boolean;
  onManageSubscription: () => void;
}

function ActionButton({
  plan,
  onManageSubscription,
}: {
  plan: Plan;
  onManageSubscription: () => void;
}) {
  if (plan === Plan.Free) {
    return (
      <Button asChild className="gap-2">
        <Link href="/pricing">
          <BsStars className="h-4 w-4" />
          Upgrade
        </Link>
      </Button>
    );
  }

  return (
    <Button variant="outline" className="gap-2" onClick={onManageSubscription}>
      <RiUserSettingsLine className="h-4 w-4" />
      Manage Subscription
    </Button>
  );
}

function SubscriptionContent({
  subscription,
  onManageSubscription,
}: {
  subscription: { plan: Plan };
  onManageSubscription: () => void;
}) {
  return (
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
        <ActionButton
          plan={subscription.plan}
          onManageSubscription={onManageSubscription}
        />
      </div>
    </div>
  );
}

export function SubscriptionDisplay({
  subscription,
  isLoading,
  onManageSubscription,
}: SubscriptionDisplayProps) {
  function renderDescription() {
    if (isLoading) {
      return (
        <div className="space-y-2 mt-1">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
      );
    }

    if (subscription) {
      return (
        <SubscriptionContent
          subscription={subscription}
          onManageSubscription={onManageSubscription}
        />
      );
    }

    return null;
  }

  return (
    <SettingsItem
      icon={BsStars}
      label="Subscription"
      description={renderDescription()}
    />
  );
}
