"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useCreateProject } from "@/hooks/use-project";
import { useMetaInfo } from "@/components/context/metainfo";
import { useRouter } from "next/navigation";

const formSchema = z.object({
  name: z.string().min(1, "Project name cannot be empty"),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateProjectDialogProps {
  onProjectCreated: () => Promise<void>;
  openDialog: boolean;
  setOpenDialog: (open: boolean) => void;
}

export function CreateProjectDialog({
  onProjectCreated,
  openDialog,
  setOpenDialog,
}: CreateProjectDialogProps) {
  const { setActiveProject } = useMetaInfo();
  const router = useRouter();
  const { mutateAsync: createProject, isPending: isProjectCreating } =
    useCreateProject();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
    },
  });

  const handleSubmit = async (values: FormValues) => {
    try {
      const newProject = await createProject({
        name: values.name,
      });
      setActiveProject(newProject);
      await onProjectCreated();
      setOpenDialog(false);
      form.reset();
      router.push("/apps");
    } catch (error) {
      console.error("create project failed:", error);
    }
  };

  return (
    <Dialog open={openDialog} onOpenChange={setOpenDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Enter a name for your new project.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Enter project name"
                      {...field}
                      disabled={isProjectCreating}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpenDialog(false)}
                disabled={isProjectCreating}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isProjectCreating}>
                {isProjectCreating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
