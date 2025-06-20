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
import {
  dashboardDateRangeAggregationSettings,
  DASHBOARD_AGGREGATION_PLACEHOLDER,
  type DashboardDateRangeOptions,
  type TableDateRangeOptions,
  DASHBOARD_AGGREGATION_OPTIONS,
  TABLE_AGGREGATION_OPTIONS,
  getDateFromOption,
} from "@/utils/date-range-utils";

type BaseDateRangeDropdownProps<T extends string> = {
  selectedOption: T;
  options: readonly T[];
  limitedOptions?: readonly T[];
  onSelectionChange: (value: T) => void;
};

const BaseDateRangeDropdown = <T extends string>({
  selectedOption,
  options,
  limitedOptions,
  onSelectionChange,
}: BaseDateRangeDropdownProps<T>) => (
  <Select value={selectedOption} onValueChange={onSelectionChange}>
    <SelectTrigger className="w-fit font-medium hover:bg-accent hover:text-accent-foreground focus:ring-0 focus:ring-offset-0">
      {selectedOption !== "All time" && <span>Past </span>}
      <SelectValue placeholder="Select" />
    </SelectTrigger>
    <SelectContent position="popper">
      {options.map((item) => {
        const isLimited = limitedOptions?.includes(item) ?? false;
        const itemNode = (
          <SelectItem key={item} value={item} disabled={isLimited}>
            {item}
          </SelectItem>
        );

        return isLimited ? (
          <HoverCard openDelay={200} key={item}>
            <HoverCardTrigger asChild>{itemNode}</HoverCardTrigger>
            <HoverCardPortal>
              <HoverCardContent className="w-60 text-sm" side="right">
                This time range is not available in this plan
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
};

export const DashboardDateRangeDropdown = ({
  selectedOption,
  setDateRangeAndOption,
}: DashboardDateRangeDropdownProps) => {
  const disabledOptions: DashboardDateRangeOptions[] = [];

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
    />
  );
};

type TableDateRangeDropdownProps = {
  selectedOption: TableDateRangeOptions;
  setDateRangeAndOption: (
    option: TableDateRangeOptions,
    date?: { from: Date; to: Date },
  ) => void;
};

export const TableDateRangeDropdown = ({
  selectedOption,
  setDateRangeAndOption,
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
    />
  );
};
