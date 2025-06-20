"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDeleteProject } from "@/hooks/use-project";
import { useMetaInfo } from "@/components/context/metainfo";
import { useRouter } from "next/navigation";

interface DeleteProjectDialogProps {
  projectName: string;
}

export function DeleteProjectDialog({ projectName }: DeleteProjectDialogProps) {
  const [confirmName, setConfirmName] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const { projects } = useMetaInfo();
  const router = useRouter();
  const { mutateAsync: deleteProject, isPending: isProjectDeleting } =
    useDeleteProject();

  const isLastProject = projects.length === 1;

  const resetForm = () => {
    setConfirmName("");
  };

  const handleDeleteProject = async () => {
    if (confirmName !== projectName) {
      toast.error("Project name does not match");
      return;
    }

    try {
      await deleteProject();
      setIsOpen(false);
      resetForm();
      router.push("/apps");
    } catch (error) {
      console.error("delete project failed:", error);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      {isLastProject ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <Button
                variant="destructive"
                className="bg-red-600 hover:bg-red-700"
                disabled={true}
              >
                Delete project
              </Button>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Cannot delete the last project</p>
          </TooltipContent>
        </Tooltip>
      ) : (
        <AlertDialogTrigger asChild>
          <Button variant="destructive" className="bg-red-600 hover:bg-red-700">
            Delete project
          </Button>
        </AlertDialogTrigger>
      )}
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Project</AlertDialogTitle>
          <AlertDialogDescription className="space-y-4">
            This will permanently delete this project (including all agents,
            configurations, API keys, linked accounts, function executions, and
            project settings).
            <br />
            <br />
            To confirm, type{" "}
            <b style={{ whiteSpace: "pre-wrap" }}>{projectName}</b> below:
            <Input
              placeholder="Enter project name to confirm"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              className="mt-2"
            />
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={resetForm}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDeleteProject}
            className="bg-red-600 hover:bg-red-700"
            disabled={isProjectDeleting || confirmName !== projectName}
          >
            {isProjectDeleting ? "Deleting..." : "Delete Project"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
