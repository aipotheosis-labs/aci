"use client";
import Image from "next/image";
// import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { IdDisplay } from "@/components/apps/id-display";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

interface AppCardComingSoonProps {
  title: string;
  description: string;
  logo: string;
}

export function AppCardComingSoon({
  title,
  description,
  logo,
}: AppCardComingSoonProps) {
  return (
    <Card className="h-[300px] flex flex-col cursor-not-allowed transition-shadow ">
      <CardHeader className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0 flex-1 mr-4">
            <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-lg">
              <Image
                src={logo}
                alt={`${title} logo`}
                fill
                className="object-contain "
              />
            </div>
            <CardTitle className="truncate text-gray-700">{title}</CardTitle>
          </div>
          <div className="shrink-0 w-24">
            <IdDisplay id={title} />
          </div>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <CardDescription className="line-clamp-2 h-10 overflow-hidden">
                {description}
              </CardDescription>
            </TooltipTrigger>
            <TooltipContent className="max-w-md">
              <p>{description}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardHeader>
      <CardContent className="mt-auto">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-gray-200 px-3 py-1 text-sm font-medium text-gray-600 border border-gray-300">
            Coming Soon
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
