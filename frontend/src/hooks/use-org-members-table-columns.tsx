import { useMemo, useState } from "react";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { OrganizationMember } from "@/lib/types/organization";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical } from "lucide-react";
import { useMetaInfo } from "@/components/context/metainfo";

const columnHelper = createColumnHelper<OrganizationMember>();

export function useOrgMembersTableColumns({
  onRemove,
  onLeave,
}: {
  onRemove: (userId: string) => void;
  onLeave: () => void;
}): ColumnDef<OrganizationMember, unknown>[] {
  const { user } = useMetaInfo();
  const [dialogState, setDialogState] = useState<{
    type: "leave" | "remove" | null;
    memberId: string | null;
    email: string | null;
  }>({
    type: null,
    memberId: null,
    email: null,
  });

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
            const isCurrentUser = member.user_id === user.userId;

            return (
              <>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0">
                      <span className="sr-only">Open menu</span>
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {isCurrentUser ? (
                      <DropdownMenuItem
                        className="text-red-600 focus:text-red-600"
                        onSelect={() => {
                          setDialogState({
                            type: "leave",
                            memberId: member.user_id,
                            email: member.email,
                          });
                        }}
                      >
                        Leave
                      </DropdownMenuItem>
                    ) : (
                      <DropdownMenuItem
                        className="text-red-600 focus:text-red-600"
                        disabled={member.role === "Owner"}
                        onSelect={() => {
                          setDialogState({
                            type: "remove",
                            memberId: member.user_id,
                            email: member.email,
                          });
                        }}
                      >
                        Remove
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>

                <AlertDialog
                  open={dialogState.type !== null}
                  onOpenChange={(open) => {
                    if (!open) {
                      setDialogState({
                        type: null,
                        memberId: null,
                        email: null,
                      });
                    }
                  }}
                >
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>
                        {dialogState.type === "leave"
                          ? "Leave Organization"
                          : "Remove Member"}
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        {dialogState.type === "leave" ? (
                          "Are you sure you want to leave this organization? This action cannot be undone."
                        ) : (
                          <>
                            Are you sure you want to remove{" "}
                            <b>{dialogState.email}</b> from the organization?
                            This action cannot be undone.
                          </>
                        )}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => {
                          if (dialogState.type === "leave") {
                            onLeave();
                          } else if (
                            dialogState.type === "remove" &&
                            dialogState.memberId
                          ) {
                            onRemove(dialogState.memberId);
                          }
                          setDialogState({
                            type: null,
                            memberId: null,
                            email: null,
                          });
                        }}
                        className="bg-red-600 hover:bg-red-700"
                      >
                        {dialogState.type === "leave" ? "Leave" : "Remove"}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </>
            );
          },
          enableGlobalFilter: false,
        }),
      ] as ColumnDef<OrganizationMember, unknown>[],
    [onRemove, onLeave, user.userId, dialogState],
  );
}
