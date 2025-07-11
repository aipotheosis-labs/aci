"use client";

import { useMetaInfo } from "@/components/context/metainfo";
import { Button } from "@/components/ui/button";
import { createCustomerPortalSession } from "@/lib/api/billing";
import { useSubscription } from "@/hooks/use-subscription";
import { useLogoutFunction } from "@propelauth/react";
import { User, Mail, LogOut } from "lucide-react";
import { updateProject } from "@/lib/api/project";
import { toast } from "sonner";
import { SettingsSection } from "@/components/settings/settings-section";
import { SettingsItem } from "@/components/settings/settings-item";
import { SubscriptionDisplay } from "@/components/settings/subscription-display";
import { ProjectNameEditor } from "@/components/settings/project-name-editor";
import { DangerZone } from "@/components/settings/danger-zone";
import { OrgMembersTable } from "@/components/settings/org-members-table";

export default function SettingsPage() {
  const { user, activeOrg, accessToken, activeProject, reloadActiveProject } =
    useMetaInfo();
  const logoutFn = useLogoutFunction();
  const { data: subscription, isLoading } = useSubscription();

  const handleSaveProjectName = async (newName: string) => {
    if (!newName.trim()) {
      toast.error("Project name cannot be empty");
      return;
    }

    try {
      await updateProject(accessToken, activeProject.id, newName);
      await reloadActiveProject();
      toast.success("Project name updated");
    } catch (error) {
      console.error("Failed to update project name:", error);
      toast.error("Failed to update project name");
    }
  };

  return (
    <div>
      <div className="m-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground">
            Manage your account, project, and organization settings in one
            place.
          </p>
        </div>
      </div>

      <div className="m-4 space-y-6">
        {/* Account Settings Section */}
        <SettingsSection
          title="Account Settings"
          description="Manage your personal account information"
        >
          <SettingsItem
            icon={User}
            label="User Name"
            description={`${user.firstName} ${user.lastName}`}
          />
          <SettingsItem icon={Mail} label="Email" description={user.email} />
          <SettingsItem
            icon={LogOut}
            label="Sign Out"
            description="Sign out of your account"
            iconClassName="text-destructive"
            containerClassName="bg-destructive/10"
          >
            <Button variant="destructive" onClick={() => logoutFn(true)}>
              Sign Out
            </Button>
          </SettingsItem>
        </SettingsSection>

        {/* Project Settings Section */}
        <SettingsSection
          title="Project Settings"
          description="Manage your project settings and preferences"
        >
          <ProjectNameEditor
            projectName={activeProject.name}
            onSave={handleSaveProjectName}
          />

          <DangerZone projectName={activeProject.name} />
        </SettingsSection>

        {/* Organization Settings Section */}
        <SettingsSection
          title="Organization Settings"
          description="Manage your organization settings and subscription"
        >
          <SettingsItem
            icon={User}
            label="Organization Name"
            description={activeOrg.orgName}
          />

          <SubscriptionDisplay
            subscription={subscription}
            isLoading={isLoading}
            onManageSubscription={async () => {
              const url = await createCustomerPortalSession(
                accessToken,
                activeOrg.orgId,
              );
              window.location.href = url;
            }}
          />
          <OrgMembersTable />
        </SettingsSection>
      </div>
    </div>
  );
}
