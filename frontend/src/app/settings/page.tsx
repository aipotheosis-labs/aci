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
import { Check, Edit2 } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { updateProject } from "@/lib/api/project";
import { toast } from "sonner";

export default function SettingsPage() {
  const { user, activeOrg, accessToken, activeProject, reloadActiveProject } =
    useMetaInfo();
  const logoutFn = useLogoutFunction();
  const [, setShowInviteModal] = useState(false);
  const [projectName, setProjectName] = useState(activeProject.name);
  const [isEditingName, setIsEditingName] = useState(false);

  const { data: subscription, isLoading } = useSubscription();

  // Update state when active project changes
  useEffect(() => {
    setProjectName(activeProject.name);
    setIsEditingName(false);
  }, [activeProject]);

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
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">Project</label>
                <p className="text-sm text-muted-foreground">
                  Manage your project settings
                </p>
              </div>
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
                  Your organization&apos;s display name
                </p>
              </div>
              <div className="flex items-center px-2">
                <span className="font-medium">{activeOrg.orgName}</span>
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
                <div>Loading...</div>
              ) : (
                <>
                  <div className="flex-1">
                    <div className="flex justify-between p-4">
                      <div>
                        <div className="font-medium">
                          You are on the {subscription?.plan} plan
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between p-4">
                      <div>
                        {subscription?.plan === "free" ? (
                          <Link href="/pricing">
                            <Button variant="outline">
                              <BsStars />
                              Subscribe Now
                            </Button>
                          </Link>
                        ) : (
                          <Button
                            variant="outline"
                            onClick={async () => {
                              const url = await createCustomerPortalSession(
                                accessToken,
                                activeOrg.orgId,
                              );
                              window.location.href = url;
                            }}
                          >
                            <RiUserSettingsLine />
                            Manage Subscription
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            <Separator />

            {/* Team Members Section */}
            <div className="flex flex-row">
              <div className="flex flex-col items-left w-80">
                <label className="font-semibold">Team Members</label>
                <p className="text-sm text-muted-foreground">
                  Manage your organization&apos;s team members
                </p>
              </div>
              <div className="flex-1 space-y-4">
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Your Role:</span>
                    <span>{activeOrg.userAssignedRole}</span>
                  </div>
                </div>
                <div className="flex flex-col gap-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowInviteModal(true)}
                    >
                      Invite Members
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        window.open("https://auth.propelauth.com/org", "_blank")
                      }
                    >
                      Manage Organization
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
