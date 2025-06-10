"use client";

import { QuotaUsage } from "@/lib/types/quota";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface QuotaUsageDisplayProps {
  quotaUsage: QuotaUsage;
}

interface QuotaItemProps {
  title: string;
  used: number;
  limit: number;
}

const QuotaItem: React.FC<QuotaItemProps> = ({ title, used, limit }) => {
  const percentage = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const isNearLimit = percentage >= 80;
  const isFull = percentage >= 100;

  // Determine progress color based on usage
  let progressClass = "text-chart-1"; // Default blue for normal usage
  if (isFull) {
    progressClass = "text-destructive"; // Red for full
  } else if (isNearLimit) {
    progressClass = "text-chart-3"; // Orange for near limit
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{title}</span>
        <Badge
          variant={
            isFull ? "destructive" : isNearLimit ? "secondary" : "default"
          }
        >
          {used}/{limit}
        </Badge>
      </div>
      <div className={progressClass}>
        <Progress value={percentage} className="h-2 [&>div]:bg-current" />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Used: {used}</span>
        <span>Remaining: {Math.max(limit - used, 0)}</span>
      </div>
    </div>
  );
};

export const QuotaUsageDisplay: React.FC<QuotaUsageDisplayProps> = ({
  quotaUsage,
}) => {
  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between p-4">
        <CardTitle>Quota Usage</CardTitle>
        <Badge variant="outline">{quotaUsage.plan.name} Plan</Badge>
      </CardHeader>
      <Separator />
      <CardContent className="p-4 space-y-6">
        <QuotaItem
          title="Projects"
          used={quotaUsage.projects_used}
          limit={quotaUsage.plan.features.projects}
        />

        <QuotaItem
          title="Linked Accounts"
          used={quotaUsage.linked_accounts_used}
          limit={quotaUsage.plan.features.linked_accounts}
        />

        <QuotaItem
          title="Agent Credentials"
          used={quotaUsage.agent_credentials_used}
          limit={quotaUsage.plan.features.agent_credentials}
        />
      </CardContent>
    </Card>
  );
};
