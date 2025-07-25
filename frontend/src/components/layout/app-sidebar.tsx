"use client";

import Link from "next/link";
import Image from "next/image";
import { GrAppsRounded } from "react-icons/gr";
// import { GoHome } from "react-icons/go";
import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";
import React from "react";
import { VscGraph } from "react-icons/vsc";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { PiStorefront } from "react-icons/pi";
import { RiSettings3Line, RiLinkUnlinkM } from "react-icons/ri";
import { AiOutlineRobot } from "react-icons/ai";
import { HiOutlineChatBubbleBottomCenterText } from "react-icons/hi2";
import { RiFileList3Line } from "react-icons/ri";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const showLogDashboard =
  process.env.NEXT_PUBLIC_FEATURE_LOG_DASHBOARD === "true";

// Export sidebar items so they can be used in header
export const sidebarItems = [
  {
    title: "App Store",
    url: `/apps`,
    icon: PiStorefront,
  },
  {
    title: "App Configurations",
    url: `/appconfigs`,
    icon: GrAppsRounded,
  },
  {
    title: "Linked Accounts",
    url: `/linked-accounts`,
    icon: RiLinkUnlinkM,
  },
  {
    title: "Agents",
    url: `/agents`,
    icon: AiOutlineRobot,
  },
  {
    title: "Agent Playground",
    url: `/playground`,
    icon: HiOutlineChatBubbleBottomCenterText,
  },
  ...(showLogDashboard
    ? [
        {
          title: "Log Dashboard",
          url: `/logs`,
          icon: RiFileList3Line,
        },
      ]
    : []),
  {
    title: "Usage",
    url: `/usage`,
    icon: VscGraph,
  },
];

// Add settings routes to be accessible in header
export const settingsItem = {
  title: "Settings",
  url: "/settings",
  icon: RiSettings3Line,
};

export function AppSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const pathname = usePathname();

  return (
    <Sidebar variant="inset" collapsible="icon" className="flex flex-col">
      <SidebarHeader className="px-2 pt-4 pb-0 gap-2 flex flex-col">
        <div
          className={cn(
            "flex items-center px-4 h-9",
            isCollapsed ? "justify-center" : "justify-between gap-2",
          )}
        >
          {!isCollapsed && (
            <div className="h-9 w-auto relative flex items-center justify-center">
              <Image
                src="/aci-dev-full-logo.svg"
                alt="ACI Dev Logo"
                width={150}
                height={30}
                priority
                className="object-contain"
              />
            </div>
          )}
          <SidebarTrigger />
        </div>
        <Separator />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {sidebarItems.map((item) => {
                const isActive =
                  pathname === item.url || pathname.startsWith(item.url);
                return (
                  <SidebarMenuItem key={item.title}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <SidebarMenuButton asChild>
                          <Link
                            href={item.url}
                            className={cn(
                              "flex items-center gap-3 px-4 py-2 transition-colors",
                              isCollapsed && "justify-center",
                              isActive &&
                                "bg-primary/10 text-primary font-medium",
                            )}
                          >
                            <item.icon
                              className={cn(
                                "h-5 w-5 shrink-0",
                                isActive && "text-primary",
                              )}
                            />
                            {!isCollapsed && <span>{item.title}</span>}
                          </Link>
                        </SidebarMenuButton>
                      </TooltipTrigger>
                      {isCollapsed && (
                        <TooltipContent side="right">
                          {item.title}
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <Tooltip>
              <TooltipTrigger asChild>
                <SidebarMenuButton asChild>
                  <Link
                    href={settingsItem.url}
                    className={cn(
                      "flex items-center gap-3 p-4 transition-colors",
                      isCollapsed && "justify-center",
                      pathname === settingsItem.url &&
                        "bg-primary/10 text-primary font-medium",
                    )}
                  >
                    {(() => {
                      const IconComponent = settingsItem.icon;
                      return (
                        <IconComponent
                          className={cn(
                            "h-5 w-5 shrink-0",
                            pathname === settingsItem.url && "text-primary",
                          )}
                        />
                      );
                    })()}
                    {!isCollapsed && <span>{settingsItem.title}</span>}
                  </Link>
                </SidebarMenuButton>
              </TooltipTrigger>
              {isCollapsed && (
                <TooltipContent side="right">
                  {settingsItem.title}
                </TooltipContent>
              )}
            </Tooltip>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
