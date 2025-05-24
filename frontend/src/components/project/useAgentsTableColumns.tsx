"use client";

import {
  createColumnHelper,
  ColumnDef,
  CellContext,
} from "@tanstack/react-table";
import { IdDisplay } from "@/components/apps/id-display";
import { Button } from "@/components/ui/button";
import { GoTrash } from "react-icons/go";
import { BsQuestionCircle } from "react-icons/bs";
import { CiEdit } from "react-icons/ci";
import { IoIosCheckmark } from "react-icons/io";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AppEditForm } from "@/components/project/app-edit-form";
import { AgentInstructionFilterForm } from "@/components/project/agent-instruction-filter-form";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { ArrowUpDown } from "lucide-react";
import { Agent } from "@/lib/types/project";
import { useState, useEffect, useMemo, useCallback } from "react";
import { toast } from "sonner";
import { useUpdateAgent } from "@/hooks/use-agent";

const EditableCell = ({
  initialValue,
  fieldName,
  agentId,
  onUpdate,
}: {
  initialValue: string;
  fieldName: string;
  agentId: string;
  onUpdate: (agentId: string, field: string, value: string) => Promise<void>;
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(initialValue);
  const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-edit-element="true"]')) {
        setIsEditing(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (isEditing && inputRef) {
      inputRef.focus();
      const length = inputRef.value.length;
      inputRef.setSelectionRange(length, length);
    }
  }, [isEditing, inputRef]);

  return (
    <div className="flex items-center space-x-2" data-edit-element="true">
      {isEditing ? (
        <>
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="h-5 p-0 w-full border-none shadow-none bg-transparent px-0 focus-visible:ring-0 focus-visible:ring-offset-0 caret-visible"
            autoFocus
            data-edit-element="true"
            ref={setInputRef}
          />
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => {
              onUpdate(agentId, fieldName, value);
              setIsEditing(false);
            }}
            data-edit-element="true"
          >
            <IoIosCheckmark className="h-5 w-5" />
          </Button>
        </>
      ) : (
        <>
          <Input
            value={initialValue}
            readOnly
            className="h-5 p-0 w-full border-none shadow-none bg-transparent px-0 focus-visible:ring-0 focus-visible:ring-offset-0 cursor-default"
            data-edit-element="true"
          />
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => {
              setValue(initialValue);
              setIsEditing(true);
            }}
            data-edit-element="true"
          >
            <CiEdit className="h-4 w-4" />
          </Button>
        </>
      )}
    </div>
  );
};

const columnHelper = createColumnHelper<Agent>();

export const useAgentsTableColumns = (
  projectId: string,
  onDeleteAgent: (agentId: string) => Promise<void>,
): ColumnDef<Agent>[] => {
  const { mutateAsync: updateAgentMutation } = useUpdateAgent();

  const handleUpdateAgent = useCallback(
    async (agentId: string, field: string, value: string) => {
      if (!projectId) return;

      try {
        const updateData: Record<string, string> = {};
        updateData[field] = value;

        await updateAgentMutation({
          id: agentId,
          data: updateData,
        });

        toast.success(`Agent ${field} updated successfully`);
      } catch (error) {
        toast.error(`Error updating agent ${field}`);
        console.error(`Error updating agent ${field}:`, error);
      }
    },
    [projectId, updateAgentMutation],
  );

  return useMemo(() => {
    return [
      columnHelper.accessor("name", {
        header: ({ column }) => (
          <div className="text-left">
            <Button
              variant="ghost"
              onClick={() =>
                column.toggleSorting(column.getIsSorted() === "asc")
              }
              className="w-full justify-start px-0"
            >
              AGENT NAME
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: (ctx: CellContext<Agent, string>) => {
          const agent = ctx.row.original;
          return (
            <EditableCell
              initialValue={agent.name}
              fieldName="name"
              agentId={agent.id}
              onUpdate={handleUpdateAgent}
            />
          );
        },
        enableGlobalFilter: true,
      }) as ColumnDef<Agent>,
      columnHelper.accessor("description", {
        header: "DESCRIPTION",
        cell: (ctx: CellContext<Agent, string>) => {
          const agent = ctx.row.original;
          return (
            <EditableCell
              initialValue={agent.description}
              fieldName="description"
              agentId={agent.id}
              onUpdate={handleUpdateAgent}
            />
          );
        },
        enableGlobalFilter: true,
      }) as ColumnDef<Agent>,
      columnHelper.accessor("api_keys", {
        header: "API KEY",
        cell: (ctx: CellContext<Agent, Agent["api_keys"]>) => (
          <div className="font-mono w-24">
            <IdDisplay id={ctx.getValue()[0].key} />
          </div>
        ),
        enableGlobalFilter: false,
      }) as ColumnDef<Agent>,
      // columnHelper.accessor("created_at", {
      //   header: ({ column }) => (
      //     <div className="text-left">
      //       <Button
      //         variant="ghost"
      //         onClick={() =>
      //           column.toggleSorting(column.getIsSorted() === "asc")
      //         }
      //         className="w-full justify-start px-0"
      //       >
      //         CREATION TIME
      //         <ArrowUpDown className="h-4 w-4" />
      //       </Button>
      //     </div>
      //   ),
      //   cell: (ctx) => (
      //     <div>
      //       {new Date(ctx.getValue())
      //         .toISOString()
      //         .replace(/\.\d{3}Z$/, "")
      //         .replace("T", " ")}
      //     </div>
      //   ),
      //   enableGlobalFilter: false,
      // }) as ColumnDef<Agent>,
      columnHelper.accessor("allowed_apps", {
        header: "ALLOWED APPS",
        cell: (ctx) => (
          <div className="text-center">
            <AppEditForm
              agentId={ctx.row.original.id}
              allowedApps={ctx.row.original.allowed_apps || []}
            >
              <Button variant="outline" size="sm" data-action="edit-apps">
                Edit
              </Button>
            </AppEditForm>
          </div>
        ),
        enableGlobalFilter: false,
      }) as ColumnDef<Agent>,
      columnHelper.accessor("custom_instructions", {
        header: () => (
          <div className="text-left w-40">
            <Tooltip>
              <TooltipTrigger className="flex items-center whitespace-nowrap gap-1">
                <span className="text-sm">CUSTOM INSTRUCTIONS</span>
                <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p>
                  Outline in natural language when an API execution request from
                  agents should be blocked.
                </p>
              </TooltipContent>
            </Tooltip>
          </div>
        ),
        cell: (ctx) => (
          <div className="text-center">
            <AgentInstructionFilterForm
              agentId={ctx.row.original.id}
              initialInstructions={ctx.row.original.custom_instructions}
              allowedApps={ctx.row.original.allowed_apps || []}
            >
              <Button variant="outline" size="sm">
                Edit
              </Button>
            </AgentInstructionFilterForm>
          </div>
        ),
        enableGlobalFilter: false,
      }) as ColumnDef<Agent>,
      columnHelper.accessor("id", {
        header: () => (
          <div className="text-left w-24">
            <Tooltip>
              <TooltipTrigger className="flex items-center whitespace-nowrap gap-1">
                <span className="text-sm">AGENT ID</span>
                <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent>
                <p>For debugging only: the unique identifier for the agent.</p>
              </TooltipContent>
            </Tooltip>
          </div>
        ),
        cell: (ctx: CellContext<Agent, string>) => (
          <div className="font-mono w-24">
            <IdDisplay id={`For Debugging Only: ${ctx.getValue()}`} />
          </div>
        ),
        enableGlobalFilter: false,
      }) as ColumnDef<Agent>,
      columnHelper.accessor((row) => row.id, {
        id: "delete",
        header: () => <div className="text-center">DELETE</div>,
        cell: (ctx) => (
          <div className="text-center">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" className="text-red-600">
                  <GoTrash />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Agent?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete
                    the agent &quot;
                    {ctx.row.original.name}
                    &quot; and remove all its associated data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => onDeleteAgent(ctx.row.original.id)}
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        ),
        enableGlobalFilter: false,
      }) as ColumnDef<Agent>,
    ];
  }, [handleUpdateAgent, onDeleteAgent]);
};
