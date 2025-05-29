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
import { deleteProject } from "@/lib/api/project";
import { useMetaInfo } from "@/components/context/metainfo";
import { useRouter } from "next/navigation";

interface DeleteProjectDialogProps {
  accessToken: string;
  projectId: string;
  projectName: string;
}

export function DeleteProjectDialog({
  accessToken,
  projectId,
  projectName,
}: DeleteProjectDialogProps) {
  console.log("projectName", projectName);
  const [isDeleting, setIsDeleting] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const { reloadActiveProject, projects } = useMetaInfo();
  const router = useRouter();

  const isLastProject = projects.length === 1;

  const resetForm = () => {
    setConfirmName("");
    setIsDeleting(false);
  };

  const handleDeleteProject = async () => {
    if (confirmName !== projectName) {
      toast.error("Project name does not match");
      return;
    }

    try {
      setIsDeleting(true);
      await deleteProject(accessToken, projectId);
      await reloadActiveProject();
      toast.success("Project deleted successfully");
      setIsOpen(false);
      resetForm();
      router.push("/apps");
    } catch (error) {
      console.error("Failed to delete project:", error);
      toast.error("Failed to delete project");
    } finally {
      setIsDeleting(false);
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
            disabled={isDeleting || confirmName !== projectName}
          >
            {isDeleting ? "Deleting..." : "Delete Project"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
