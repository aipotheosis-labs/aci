"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OrganizationMember, OrganizationRole } from "@/lib/types/organization";
import {
  listOrganizationMembers,
  inviteToOrganization,
  removeMember,
  leaveOrganization,
} from "@/lib/api/organization";
import { Badge } from "@/components/ui/badge";
import { User2, MoreHorizontal, Plus } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useMetaInfo } from "@/components/context/metainfo";
import { toast } from "sonner";
import { useOrgHelper } from "@propelauth/react";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { createColumnHelper } from "@tanstack/react-table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ColumnDef } from "@tanstack/react-table";

interface OrganizationMembersProps {
  className?: string;
}

export function OrganizationMembers({ className }: OrganizationMembersProps) {
  const router = useRouter();
  const { user, activeOrg, accessToken } = useMetaInfo();
  const { orgHelper } = useOrgHelper();
  const org = orgHelper?.getOrg(activeOrg.orgId);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<OrganizationRole>(
    OrganizationRole.Member,
  );
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const [userSearch, setUserSearch] = useState("");

  const isAdmin =
    org?.userAssignedRole === OrganizationRole.Admin ||
    org?.userAssignedRole === OrganizationRole.Owner;
  const isOwner = org?.userAssignedRole === OrganizationRole.Owner;


  const loadMembers = async () => {
    try {
      const data = await listOrganizationMembers(accessToken, activeOrg.orgId);
      setMembers(data);
    } catch {
      toast.error("Failed to load organization members");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const handleInvite = async () => {
    try {
      await inviteToOrganization(
        accessToken,
        activeOrg.orgId,
        inviteEmail,
        inviteRole,
      );
      toast.success("Invitation sent successfully");
      setIsInviteDialogOpen(false);
      setInviteEmail("");
      loadMembers();
    } catch {
      toast.error("Failed to send invitation");
    }
  };

  const handleRemoveMember = async (userId: string) => {
    try {
      await removeMember(accessToken, activeOrg.orgId, userId);
      toast.success("Member removed successfully");
      loadMembers();
    } catch {
      toast.error("Failed to remove member");
    }
  };

  const handleLeave = async () => {
    try {
      await leaveOrganization(accessToken, activeOrg.orgId);
      toast.success("You have left the organization");
      router.push("/");
    } catch {
      toast.error("Failed to leave organization");
    }
  };

  const columnHelper = createColumnHelper<OrganizationMember>();
  const columns = [
    columnHelper.accessor("email", {
      header: () => <span>Email</span>,
      cell: (info) => (
        <div className="flex items-center gap-2 font-medium text-foreground">
          <User2 className="h-5 w-5 text-muted-foreground" />
          {info.getValue()}
        </div>
      ),
      enableGlobalFilter: true,
    }) as ColumnDef<OrganizationMember, string>,
    columnHelper.accessor("role", {
      header: () => <span>Role</span>,
      cell: (info) => {
        const member = info.row.original;
        if (!isAdmin || member.user_id === user.userId) {
          return <Badge variant="secondary">{member.role}</Badge>;
        }
        return (
          <Select
            value={member.role}
            onValueChange={(value) => {
              // TODO: Implement role change
              console.log("Role changed to:", value);
            }}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Member">Member</SelectItem>
              <SelectItem value="Admin">Admin</SelectItem>
              {isOwner && <SelectItem value="Owner">Owner</SelectItem>}
            </SelectContent>
          </Select>
        );
      },
    }) as ColumnDef<OrganizationMember, OrganizationRole>,
    columnHelper.display({
      id: "actions",
      header: () => null,
      cell: (info) => {
        const member = info.row.original;
        if (!isAdmin || member.user_id === user.userId) return null;

        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => handleRemoveMember(member.user_id)}
              >
                Remove Member
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    }) as ColumnDef<OrganizationMember, unknown>,
  ];

  const filteredMembers = members.filter((member) =>
    member.email.toLowerCase().includes(userSearch.toLowerCase()),
  );

  return (
    <div className={className}>
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-semibold">Organization Members</h2>
          <p className="text-sm text-muted-foreground">
            Manage your organization members and their roles
          </p>
        </div>
        {isAdmin && (
          <Dialog
            open={isInviteDialogOpen}
            onOpenChange={setIsInviteDialogOpen}
          >
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Invite Member
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Member</DialogTitle>
                <DialogDescription>
                  Send an invitation to join your organization
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="Enter email address"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={inviteRole}
                    onValueChange={(value) =>
                      setInviteRole(value as OrganizationRole)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Member">Member</SelectItem>
                      <SelectItem value="Admin">Admin</SelectItem>
                      {isOwner && <SelectItem value="Owner">Owner</SelectItem>}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsInviteDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleInvite}>Send Invitation</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>
      <div className="mt-4">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Input
                placeholder="Search by email"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="w-72 bg-background border border-muted text-foreground placeholder:text-muted-foreground rounded-md shadow-none"
              />
            </div>
            <EnhancedDataTable
              data={filteredMembers}
              columns={columns}
              searchBarProps={undefined}
              paginationOptions={undefined}
            />
            {!isOwner && (
              <div className="mt-4">
                <Button variant="destructive" onClick={handleLeave}>
                  Leave Organization
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
