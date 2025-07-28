"use client";
import Image from "next/image";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { type App } from "@/lib/types/app";
import { IdDisplay } from "@/components/apps/id-display";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";
import { useAppLinkedAccounts } from "@/hooks/use-linked-account";
import { Badge } from "@/components/ui/badge";
import { CheckCircle } from "lucide-react";

interface AppCardProps {
  app: App;
  isConfigured?: boolean;
}

export function AppCard({ app, isConfigured = false }: AppCardProps) {
  const { data: linkedAccounts = [] } = useAppLinkedAccounts(app.name);
  return (
    <Link href={`/apps/${app.name}`} className="block">
      <Card className="h-[300px] transition-shadow hover:shadow-lg flex flex-col overflow-hidden relative">
        {isConfigured && (
          <div className="absolute top-2 right-2 z-10">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge
                    variant="secondary"
                    className="bg-green-100 text-green-700 border-green-200 flex items-center gap-1"
                  >
                    <CheckCircle className="h-3 w-3" />
                    Configured
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p>App already configured for this project</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}

        <CardHeader className="space-y-4">
          <div className="flex items-center justify-between min-w-0">
            <div className="flex items-center gap-3 min-w-0 flex-1 mr-4">
              <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg">
                <Image
                  src={app.logo}
                  alt={`${app.name} logo`}
                  fill
                  className="object-contain"
                />
              </div>
              <CardTitle className="truncate">{app.display_name}</CardTitle>
            </div>
            <div className="shrink-0 w-24">
              <IdDisplay id={app.name} />
            </div>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <CardDescription className="line-clamp-4  overflow-hidden">
                  {app.description}
                </CardDescription>
              </TooltipTrigger>
              <TooltipContent className="max-w-md">
                <p>{app.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardHeader>
        <CardContent className="mt-auto flex justify-between">
          <div className="flex flex-wrap items-start gap-2  ">
            {app.categories.map((category) => (
              <span
                key={category}
                className="rounded-md bg-gray-100 px-3 py-1 text-sm font-medium text-gray-600 border border-gray-200"
              >
                {category}
              </span>
            ))}
          </div>
          <TooltipProvider>
            <div className="flex justify-end  items-end  flex-wrap gap-2  ">
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-sm bg-gray-100 px-2.5 py-1 font-medium text-gray-600 border rounded-full border-gray-200">
                    {app.functions.length}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">
                    {`Functions in This App: ${app.functions.length}`}
                  </p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-sm bg-blue-100 px-2.5 py-1 font-medium text-blue-600 border rounded-full border-blue-200">
                    {linkedAccounts.length}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">
                    {`Linked Accounts: ${linkedAccounts.length}`}
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        </CardContent>
      </Card>
    </Link>
  );
}
