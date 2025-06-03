import { useMemo } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { OrganizationMember } from "@/lib/types/organization";
import { Button } from "@/components/ui/button";

const columnHelper = createColumnHelper<OrganizationMember>();

export function useOrgMembersTableColumns({
  onRemove,
}: {
  onRemove: (userId: string) => void;
}): ColumnDef<OrganizationMember>[] {
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
              <Button
                variant="ghost"
                size="sm"
                className="text-red-600"
                onClick={() => onRemove(member.user_id)}
                disabled={member.role === "Owner"}
                title={
                  member.role === "Owner"
                    ? "Cannot remove owner"
                    : "Remove member"
                }
              >
                Remove
              </Button>
            );
          },
          enableGlobalFilter: false,
        }),
      ] as ColumnDef<OrganizationMember, unknown>[],
    [onRemove],
  );
}
