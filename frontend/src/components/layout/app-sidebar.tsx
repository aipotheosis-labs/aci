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
import { ProjectSelector } from "./project-selector";
import { PiStorefront } from "react-icons/pi";
import {
  RiSettings3Line,
  RiSettings4Line,
  RiLinkUnlinkM,
} from "react-icons/ri";
import { AiOutlineExperiment } from "react-icons/ai";
import { HiOutlineChatBubbleBottomCenterText } from "react-icons/hi2";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Export sidebar items so they can be used in header
export const sidebarItems = [
  // {
  //   title: "Home",
  //   url: `/home`,
  //   icon: GoHome,
  // },
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
    icon: AiOutlineExperiment,
  },
  {
    title: "Agent Playground",
    url: `/playground`,
    icon: HiOutlineChatBubbleBottomCenterText,
  },
  {
    title: "Usage",
    url: `/usage`,
    icon: VscGraph,
  },
];

// Add settings routes to be accessible in header
export const settingsItems = [
  {
    title: "Manage Project",
    url: "/project-setting",
    icon: RiSettings3Line,
  },
  {
    title: "Account Settings",
    url: "/account",
    icon: RiSettings4Line,
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const pathname = usePathname();

  return (
    <Sidebar variant="inset" collapsible="icon" className="flex flex-col">
      <div className="w-full text-center py-1 text-xs font-bold flex items-center justify-center border-b-2 border-gray-200">
        <AiOutlineExperiment className="inline-block mr-2" />
        In Beta
      </div>
      <SidebarHeader>
        <div
          className={cn(
            "flex items-center px-4",
            isCollapsed ? "justify-center" : "justify-between gap-2",
          )}
        >
          {!isCollapsed && (
            <div className="h-8 w-auto relative flex items-center justify-center">
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
        <div
          className={cn(
            "transition-all duration-200 overflow-hidden",
            isCollapsed
              ? "max-h-0 opacity-0 scale-95"
              : "max-h-[100px] opacity-100 scale-100",
          )}
        >
          <div className="w-full p-4">
            <ProjectSelector />
          </div>
          <Separator />
        </div>
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
                                "h-5 w-5 flex-shrink-0",
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
                    href={settingsItems[0].url}
                    className={cn(
                      "flex items-center gap-3 p-4 transition-colors",
                      isCollapsed && "justify-center",
                      pathname === settingsItems[0].url &&
                        "bg-primary/10 text-primary font-medium",
                    )}
                  >
                    {(() => {
                      const IconComponent = settingsItems[0].icon;
                      return (
                        <IconComponent
                          className={cn(
                            "h-5 w-5 flex-shrink-0",
                            pathname === settingsItems[0].url && "text-primary",
                          )}
                        />
                      );
                    })()}
                    {!isCollapsed && <span>{settingsItems[0].title}</span>}
                  </Link>
                </SidebarMenuButton>
              </TooltipTrigger>
              {isCollapsed && (
                <TooltipContent side="right">
                  {settingsItems[0].title}
                </TooltipContent>
              )}
            </Tooltip>
          </SidebarMenuItem>
        </SidebarMenu>

        <Separator />

        <SidebarMenu>
          <SidebarMenuItem>
            <Tooltip>
              <TooltipTrigger asChild>
                <SidebarMenuButton asChild>
                  <Link
                    href={settingsItems[1].url}
                    className={cn(
                      "flex items-center gap-3 p-4 transition-colors",
                      isCollapsed && "justify-center",
                      pathname === settingsItems[1].url &&
                        "bg-primary/10 text-primary font-medium",
                    )}
                  >
                    {(() => {
                      const IconComponent = settingsItems[1].icon;
                      return (
                        <IconComponent
                          className={cn(
                            "h-5 w-5 flex-shrink-0",
                            pathname === settingsItems[1].url && "text-primary",
                          )}
                        />
                      );
                    })()}
                    {!isCollapsed && <span>{settingsItems[1].title}</span>}
                  </Link>
                </SidebarMenuButton>
              </TooltipTrigger>
              {isCollapsed && (
                <TooltipContent side="right">
                  {settingsItems[1].title}
                </TooltipContent>
              )}
            </Tooltip>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
