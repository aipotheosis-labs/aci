"use client";

import * as React from "react";
import { addMinutes } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { HoverCardPortal } from "@radix-ui/react-hover-card";
import { Badge } from "@/components/ui/badge";
import { Crown } from "lucide-react";
import {
  dashboardDateRangeAggregationSettings,
  DASHBOARD_AGGREGATION_PLACEHOLDER,
  type DashboardDateRangeOptions,
  type TableDateRangeOptions,
  type DashboardDateRangeAggregationOption,
  DASHBOARD_AGGREGATION_OPTIONS,
  TABLE_AGGREGATION_OPTIONS,
  getDateFromOption,
  getMinimumPlanForOption,
  getOptionDescription,
} from "@/utils/date-range-utils";

type BaseDateRangeDropdownProps<T extends string> = {
  selectedOption: T;
  options: readonly T[];
  limitedOptions?: readonly T[];
  onSelectionChange: (value: T) => void;
  userRetentionDays?: number;
};

const BaseDateRangeDropdown = <T extends string>({
  selectedOption,
  options,
  limitedOptions,
  onSelectionChange,
  userRetentionDays,
}: BaseDateRangeDropdownProps<T>) => (
  <Select value={selectedOption} onValueChange={onSelectionChange}>
    <SelectTrigger className="w-fit font-medium hover:bg-accent hover:text-accent-foreground focus:ring-0 focus:ring-offset-0">
      {selectedOption !== "All time" && <span>Past &nbsp;</span>}
      <SelectValue placeholder="Select" />
    </SelectTrigger>
    <SelectContent position="popper">
      {options.map((item) => {
        const isLimited = limitedOptions?.includes(item) ?? false;
        const isDashboardOption = DASHBOARD_AGGREGATION_OPTIONS.includes(
          item as DashboardDateRangeAggregationOption,
        );

        // Get plan information for dashboard options
        let planInfo = null;
        let description = null;
        if (isDashboardOption && item !== DASHBOARD_AGGREGATION_PLACEHOLDER) {
          try {
            planInfo = getMinimumPlanForOption(
              item as DashboardDateRangeAggregationOption,
            );
            description = getOptionDescription(
              item as DashboardDateRangeAggregationOption,
              userRetentionDays,
            );
          } catch {
            // Fallback for options not in settings
          }
        }

        const itemNode = (
          <SelectItem
            key={item}
            value={item}
            disabled={isLimited}
            className={`${isLimited ? "opacity-50" : ""} py-2 w-full`}
          >
            <div className="flex items-center justify-between w-full">
              <div className="font-normal pr-2">{item}</div>
              {isLimited && planInfo && (
                <Badge variant={"outline"} className="text-xs py-0.5">
                  {planInfo.planDisplayName}
                </Badge>
              )}
            </div>
          </SelectItem>
        );

        return isLimited ? (
          <HoverCard openDelay={200} key={item}>
            <HoverCardTrigger asChild>{itemNode}</HoverCardTrigger>
            <HoverCardPortal>
              <HoverCardContent className="w-80 p-4" side="right">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">
                      Time Range Not Available
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {description ||
                      `This time range requires ${planInfo?.planDisplayName || "a higher"} plan with ${planInfo?.retentionDays || "extended"} days log retention.`}
                  </p>
                  {planInfo && (
                    <div className="flex items-center gap-2 mt-2 pt-2 border-t">
                      <Crown className="h-4 w-4 text-primary" />
                      <span className="text-xs text-muted-foreground">
                        Upgrade to {planInfo.planDisplayName} plan to access
                        this feature
                      </span>
                    </div>
                  )}
                </div>
              </HoverCardContent>
            </HoverCardPortal>
          </HoverCard>
        ) : (
          itemNode
        );
      })}
    </SelectContent>
  </Select>
);

type DashboardDateRangeDropdownProps = {
  selectedOption: DashboardDateRangeOptions;
  setDateRangeAndOption: (
    option: DashboardDateRangeOptions,
    date?: { from: Date; to: Date },
  ) => void;
  logRetentionDays?: number;
};

export const DashboardDateRangeDropdown = ({
  selectedOption,
  setDateRangeAndOption,
  logRetentionDays,
}: DashboardDateRangeDropdownProps) => {
  // Calculate disabled options based on log retention days
  const disabledOptions: DashboardDateRangeOptions[] = [];

  if (logRetentionDays) {
    DASHBOARD_AGGREGATION_OPTIONS.forEach((option) => {
      const setting = dashboardDateRangeAggregationSettings[option];
      if (setting && setting.minutes > logRetentionDays * 24 * 60) {
        disabledOptions.push(option);
      }
    });
  }

  const onDropDownSelection = (value: DashboardDateRangeOptions) => {
    if (value === DASHBOARD_AGGREGATION_PLACEHOLDER) {
      setDateRangeAndOption(DASHBOARD_AGGREGATION_PLACEHOLDER, undefined);
      return;
    }
    const setting =
      dashboardDateRangeAggregationSettings[
        value as keyof typeof dashboardDateRangeAggregationSettings
      ];
    setDateRangeAndOption(value, {
      from: addMinutes(new Date(), -setting.minutes),
      to: new Date(),
    });
  };

  const options =
    selectedOption === DASHBOARD_AGGREGATION_PLACEHOLDER
      ? [...DASHBOARD_AGGREGATION_OPTIONS, DASHBOARD_AGGREGATION_PLACEHOLDER]
      : [...DASHBOARD_AGGREGATION_OPTIONS];

  return (
    <BaseDateRangeDropdown
      selectedOption={selectedOption}
      options={options}
      limitedOptions={disabledOptions}
      onSelectionChange={onDropDownSelection}
      userRetentionDays={logRetentionDays}
    />
  );
};

type TableDateRangeDropdownProps = {
  selectedOption: TableDateRangeOptions;
  setDateRangeAndOption: (
    option: TableDateRangeOptions,
    date?: { from: Date; to: Date },
  ) => void;
  logRetentionDays?: number;
};

export const TableDateRangeDropdown = ({
  selectedOption,
  setDateRangeAndOption,
  logRetentionDays,
}: TableDateRangeDropdownProps) => {
  const disabledOptions: TableDateRangeOptions[] = [];

  const onDropDownSelection = (value: TableDateRangeOptions) => {
    const dateFromOption = getDateFromOption({
      filterSource: "TABLE",
      option: value,
    });
    const initialDateRange = dateFromOption
      ? { from: dateFromOption, to: new Date() }
      : undefined;
    setDateRangeAndOption(value, initialDateRange);
  };

  return (
    <BaseDateRangeDropdown
      selectedOption={selectedOption}
      options={TABLE_AGGREGATION_OPTIONS}
      limitedOptions={disabledOptions}
      onSelectionChange={onDropDownSelection}
      userRetentionDays={logRetentionDays}
    />
  );
};
