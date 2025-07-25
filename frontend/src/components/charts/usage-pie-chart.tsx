import { Pie, PieChart } from "recharts";

import {
  ChartConfig,
  ChartContainer,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartLegend } from "@/components/ui/chart";
import { Separator } from "@/components/ui/separator";

interface PieChartProps {
  title: string;
  cutoff: number;
  data: {
    name: string;
    value: number;
  }[];
}

export default function UsagePieChart({ title, cutoff, data }: PieChartProps) {
  // Process data to combine entries beyond cutoff into "Other" category
  const processedData =
    data.length > cutoff + 1
      ? [
          ...data.slice(0, cutoff),
          {
            name: "Other",
            value: data
              .slice(cutoff)
              .reduce((sum, item) => sum + item.value, 0),
          },
        ]
      : data;

  const chartData = processedData.map((item, index) => ({
    name: item.name,
    value: item.value,
    fill: `hsl(var(--chart-${(index % 5) + 1}))`,
  }));

  const chartConfig = {
    ...Object.fromEntries(
      chartData.map(({ name }, index) => [
        name,
        { label: name, color: `hsl(var(--chart-${(index % 5) + 1}))` },
      ]),
    ),
  } satisfies ChartConfig;

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="items-center p-4">
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <Separator />
      {data.length > 0 ? (
        <CardContent className="flex-1 pb-0">
          <ChartContainer
            config={chartConfig}
            className="mx-auto w-full h-full min-h-[200px] max-h-[300px]"
          >
            <PieChart width={400} height={300}>
              <Pie
                data={chartData}
                nameKey="name"
                dataKey="value"
                cx="50%"
                cy="50%"
                outerRadius="80%"
                label={false}
              />
              <ChartTooltip content={<ChartTooltipContent labelKey="name" />} />
              <ChartLegend
                content={<ChartLegendContent nameKey="name" />}
                className="-translate-y-2 flex-wrap gap-2 *:basis-1/4 *:justify-center max-h-20 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-muted [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar]:opacity-0 hover:[&::-webkit-scrollbar]:opacity-100 transition-opacity"
              />
            </PieChart>
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
