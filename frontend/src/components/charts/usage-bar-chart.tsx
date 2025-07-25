"use client";

import { Bar, BarChart, CartesianGrid, XAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Separator } from "@/components/ui/separator";

interface ChartDataPoint {
  date: string;
  [key: string]: number | string | undefined;
}

interface UsageBarChartProps {
  title: string;
  data: ChartDataPoint[];
}

export function UsageBarChart({ title, data }: UsageBarChartProps) {
  // Sort data by date
  const sortedData = [...data].sort((a, b) => {
    const dateA = new Date(a.date);
    const dateB = new Date(b.date);
    return dateA.getTime() - dateB.getTime();
  });

  // Get all unique app names from the data
  const appNames = Array.from(
    new Set(
      sortedData.flatMap((item) =>
        Object.keys(item).filter((key) => key !== "date"),
      ),
    ),
  );

  // Create chart config for each app
  const chartConfig = {
    ...Object.fromEntries(
      appNames.map((app, index) => [
        app,
        {
          label: app,
          color: `hsl(var(--chart-${(index % 5) + 1}))`,
        },
      ]),
    ),
  } satisfies ChartConfig;

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="flex flex-row items-center justify-between p-4">
        <div>
          <CardTitle>{title}</CardTitle>
        </div>
      </CardHeader>
      <Separator />
      {data.length > 0 ? (
        <CardContent className="flex-1 pb-0">
          <ChartContainer
            config={chartConfig}
            className="mx-auto w-full h-full min-h-[200px] max-h-[300px]"
          >
            <BarChart
              data={sortedData}
              margin={{ top: 30, right: 10, left: 10, bottom: 50 }}
              width={500}
              height={300}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="rgba(0,0,0,0.1)"
              />
              <XAxis
                dataKey="date"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                padding={{ left: 10, right: 10 }}
              />
              <ChartTooltip content={<ChartTooltipContent />} />
              {appNames.map((app, index) => (
                <Bar
                  key={app}
                  dataKey={app}
                  stackId="a"
                  fill={`hsl(var(--chart-${(index % 5) + 1}))`}
                  isAnimationActive={false}
                />
              ))}
              <ChartLegend
                content={<ChartLegendContent />}
                verticalAlign="bottom"
                height={30}
                className="-translate-y-2 flex-wrap gap-2 *:basis-1/4 *:justify-center max-h-12 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-muted [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:opacity-0 hover:[&::-webkit-scrollbar]:opacity-100 transition-opacity"
              />
            </BarChart>
          </ChartContainer>
        </CardContent>
      ) : (
        <CardContent className="flex-1 pb-0">
          <div className="flex items-center justify-center h-full min-h-[200px] max-h-[300px]">
            <p className="text-muted-foreground">
              No usage data in the last 7 days
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
