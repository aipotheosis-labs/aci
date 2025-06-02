"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { createCustomerPortalSession } from "@/lib/api/billing";
import { useSubscription } from "@/hooks/use-subscription";
import { useLogoutFunction } from "@propelauth/react";
import Link from "next/link";
import { BsStars } from "react-icons/bs";
import { RiUserSettingsLine } from "react-icons/ri";
import { useState, useEffect } from "react";
import { Check, Edit2, MoreHorizontal, User2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { updateProject } from "@/lib/api/project";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";

export default function SettingsPage() {
  const { user, activeOrg, accessToken, activeProject, reloadActiveProject } =
    useMetaInfo();
  const logoutFn = useLogoutFunction();
  const [projectName, setProjectName] = useState(activeProject.name);
  const [isEditingName, setIsEditingName] = useState(false);
  const [orgName, setOrgName] = useState(activeOrg.orgName);
  const [isEditingOrgName, setIsEditingOrgName] = useState(false);

  const { data: subscription, isLoading } = useSubscription();

  // Update state when active project changes
  useEffect(() => {
    setProjectName(activeProject.name);
    setIsEditingName(false);
  }, [activeProject]);

  // Update state when active org changes
  useEffect(() => {
    setOrgName(activeOrg.orgName);
    setIsEditingOrgName(false);
  }, [activeOrg]);

  const handleSaveProjectName = async () => {
    if (!projectName.trim()) {
      toast.error("Project name cannot be empty");
      return;
    }

    // Only update if the name has actually changed
    if (projectName === activeProject.name) {
      setIsEditingName(false);
      return;
    }

    try {
      await updateProject(accessToken, activeProject.id, projectName);
      await reloadActiveProject();
      setIsEditingName(false);
      toast.success("Project name updated");
    } catch (error) {
      console.error("Failed to update project name:", error);
      toast.error("Failed to update project name");
    }
  };

  const handleSaveOrgName = async () => {
    if (!orgName.trim()) {
      toast.error("Organization name cannot be empty");
      return;
    }

    // Only update if the name has actually changed
    if (orgName === activeOrg.orgName) {
      setIsEditingOrgName(false);
      return;
    }

    try {
      // TODO: Add API call to update organization name
      // await updateOrganization(accessToken, activeOrg.orgId, orgName);
      setIsEditingOrgName(false);
      toast.success("Organization name updated");
    } catch (error) {
      console.error("Failed to update organization name:", error);
      toast.error("Failed to update organization name");
    }
  };

  // Mock users data
  const [userSearch, setUserSearch] = useState("");
  const [users, setUsers] = useState([
    {
      email: "alex@aipolabs.xyz",
      role: "Owner",
      status: "ACTIVE",
    },
    // Add more users as needed
  ]);
  const filteredUsers = users.filter((u) =>
    u.email.toLowerCase().includes(userSearch.toLowerCase()),
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const userColumnHelper = createColumnHelper<any>();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const userColumns: ColumnDef<any>[] = [
    userColumnHelper.accessor("email", {
      header: () => <span>Email</span>,
      cell: (info) => (
        <div className="flex items-center gap-2 font-medium text-foreground">
          <User2 className="h-5 w-5 text-muted-foreground" />
          {String(info.getValue())}
        </div>
      ),
      enableGlobalFilter: true,
    }),
    userColumnHelper.accessor("role", {
      header: () => <span>Role</span>,
      cell: (info) => {
        const idx = users.findIndex(
          (u) => u.email === String(info.row.original.email),
        );
        return (
          <select
            className="bg-muted/40 border border-muted text-foreground rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary/40"
            value={String(info.getValue())}
            onChange={(e) => {
              const newUsers = [...users];
              newUsers[idx].role = e.target.value;
              setUsers(newUsers);
            }}
          >
            <option value="Owner">Owner</option>
            <option value="Admin">Admin</option>
            <option value="Member">Member</option>
          </select>
        );
      },
    }),
    userColumnHelper.accessor("status", {
      header: () => <span>Status</span>,
      cell: (info) => (
        <Badge
          className={`text-xs px-3 py-1 rounded-full font-semibold ${String(info.getValue()) === "ACTIVE" ? "bg-green-600 text-white" : "bg-muted text-muted-foreground"}`}
        >
          {String(info.getValue())}
        </Badge>
      ),
    }),
    userColumnHelper.display({
      id: "actions",
      header: () => null,
      cell: () => (
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:bg-muted/40"
        >
          <MoreHorizontal className="h-5 w-5" />
        </Button>
      ),
    }),
  ];

  return (
    <div>
      <div className="mx-4 py-6">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account, project, and organization settings in one place.
        </p>
      </div>

      <Separator />

      <div className="container p-4 space-y-8">
        {/* Account Settings Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Account Settings</h2>
          <div className="space-y-4">
            {/* User Details Section */}
            <div className="flex flex-row">
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">User Name</label>
              </div>
              <div className="flex items-center px-2">{`${user.firstName} ${user.lastName}`}</div>
            </div>

            <Separator />

            <div className="flex flex-row">
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">Email</label>
              </div>
              <div className="flex items-center px-2">{user.email}</div>
            </div>

            <Separator />

            {/* Danger Zone */}
            <div className="flex flex-row">
              <div>
                <Button variant="destructive" onClick={() => logoutFn(true)}>
                  Sign Out
                </Button>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-8" />

        {/* Project Settings Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Project Settings</h2>
          <div className="space-y-4">
            <div className="flex flex-row">
              <div className="flex-1 space-y-6">
                {/* Project Name Section */}
                <div className="flex flex-row">
                  <div className="flex flex-col items-left w-80">
                    <label className="font-semibold">Project Name</label>
                    <p className="text-sm text-muted-foreground">
                      Change the name of the project
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Input
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        className="w-96"
                        disabled={!isEditingName}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            handleSaveProjectName();
                          } else if (e.key === "Escape") {
                            setIsEditingName(false);
                            setProjectName(activeProject.name);
                          }
                        }}
                      />
                    </div>
                    {isEditingName ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleSaveProjectName}
                        className="h-8 w-8 p-0"
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            onClick={() => setIsEditingName(true)}
                            className="h-8 w-8 p-0"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Click to edit project name</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-8" />

        {/* Organization Settings Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Organization Settings</h2>
          <div className="space-y-4">
            {/* Organization Name Section */}
            <div className="flex flex-row">
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">Organization Name</label>
                <p className="text-sm text-muted-foreground">
                  Change the name of the organization
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Input
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    className="w-96"
                    disabled={!isEditingOrgName}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleSaveOrgName();
                      } else if (e.key === "Escape") {
                        setIsEditingOrgName(false);
                        setOrgName(activeOrg.orgName);
                      }
                    }}
                  />
                </div>
                {isEditingOrgName ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleSaveOrgName}
                    className="h-8 w-8 p-0"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                ) : (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        onClick={() => setIsEditingOrgName(true)}
                        className="h-8 w-8 p-0"
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Click to edit organization name</p>
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>

            <Separator />

            {/* Subscription Section */}
            <div className="flex flex-row">
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">Subscription</label>
                <p className="text-sm text-muted-foreground">
                  Manage your organization&apos;s subscription
                </p>
              </div>
              {isLoading ? (
                <div className="flex-1">
                  <div className="animate-pulse flex space-x-4">
                    <div className="flex-1 space-y-4 py-1">
                      <div className="h-4 bg-muted rounded w-3/4"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-muted rounded"></div>
                        <div className="h-4 bg-muted rounded w-5/6"></div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1">
                  <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
                      <div className="space-y-1">
                        <div className="font-medium text-lg">
                          {subscription?.plan === "free"
                            ? "Free Plan"
                            : "Pro Plan"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {subscription?.plan === "free"
                            ? "Basic features for small teams"
                            : "Advanced features for growing organizations"}
                        </div>
                      </div>
                      <div>
                        {subscription?.plan === "free" ? (
                          <Link href="/pricing">
                            <Button className="gap-2">
                              <BsStars className="h-4 w-4" />
                              Upgrade
                            </Button>
                          </Link>
                        ) : (
                          <Button
                            variant="outline"
                            className="gap-2"
                            onClick={async () => {
                              const url = await createCustomerPortalSession(
                                accessToken,
                                activeOrg.orgId,
                              );
                              window.location.href = url;
                            }}
                          >
                            <RiUserSettingsLine className="h-4 w-4" />
                            Manage Subscription
                          </Button>
                        )}
                      </div>
                    </div>
                    {subscription?.plan !== "free" && (
                      <div className="text-sm text-muted-foreground px-4">
                        Need help with your subscription?{" "}
                        <Link
                          href="/support"
                          className="text-primary hover:underline"
                        >
                          Contact support
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Team Members Table Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Button variant="outline" className="font-semibold">
                  + Invite user
                </Button>
                <Input
                  placeholder="Search by email"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-72 bg-background border border-muted text-foreground placeholder:text-muted-foreground rounded-md shadow-none"
                />
              </div>
              <div>
                <EnhancedDataTable
                  data={filteredUsers}
                  columns={userColumns}
                  searchBarProps={undefined}
                  paginationOptions={undefined}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
