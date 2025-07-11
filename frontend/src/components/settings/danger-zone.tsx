import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { DeleteProjectDialog } from "@/components/project/delete-project-dialog";

export function DangerZone({ projectName }: { projectName: string }) {
  return (
    <div className="mt-4">
      <h2 className="text-lg font-semibold mb-4">Danger Zone</h2>
      <Alert variant="destructive" className="bg-destructive/5">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Delete this project</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span className="text-sm text-destructive/90">
            Once you delete a project, there is no going back. This action
            permanently deletes the project and all related data.
          </span>
          <DeleteProjectDialog projectName={projectName} />
        </AlertDescription>
      </Alert>
    </div>
  );
}
