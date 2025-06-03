import { useMemo } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { OrganizationMember } from "@/lib/types/organization";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";

const columnHelper = createColumnHelper<OrganizationMember>();

export function useOrgMembersTableColumns({
  onRemove,
}: {
  onRemove: (userId: string) => void;
}): ColumnDef<OrganizationMember, unknown>[] {
  return useMemo(
    () =>
      [
        columnHelper.accessor("email", {
          header: "Email",
          cell: (info) => info.getValue(),
          enableGlobalFilter: true,
        }),
        columnHelper.accessor("role", {
          header: "Role",
          cell: (info) => info.getValue(),
          enableGlobalFilter: true,
        }),
        columnHelper.display({
          id: "actions",
          header: "",
          cell: (info) => {
            const member = info.row.original;
            return (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600"
                    disabled={member.role === "Owner"}
                    title={
                      member.role === "Owner"
                        ? "Cannot remove owner"
                        : "Remove member"
                    }
                  >
                    Remove
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Remove Member</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to remove <b>{member.email}</b> from
                      the organization? This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => onRemove(member.user_id)}
                      className="bg-red-600 hover:bg-red-700"
                    >
                      Remove
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            );
          },
          enableGlobalFilter: false,
        }),
      ] as ColumnDef<OrganizationMember, unknown>[],
    [onRemove],
  );
}
