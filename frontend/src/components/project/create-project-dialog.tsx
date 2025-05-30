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
import { toast } from "sonner";
import { createProject } from "@/lib/api/project";
import { useMetaInfo } from "@/components/context/metainfo";
import { useRouter } from "next/navigation";
import { useState } from "react";

const formSchema = z.object({
  name: z.string().min(1, "Project name cannot be empty"),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateProjectDialogProps {
  accessToken: string;
  orgId: string;
  onProjectCreated: () => Promise<void>;
  openDialog: boolean;
  setOpenDialog: (open: boolean) => void;
}

export function CreateProjectDialog({
  accessToken,
  orgId,
  onProjectCreated,
  openDialog,
  setOpenDialog,
}: CreateProjectDialogProps) {
  const { setActiveProject } = useMetaInfo();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
    },
  });

  const handleSubmit = async (values: FormValues) => {
    try {
      setIsCreating(true);
      const newProject = await createProject(accessToken, values.name, orgId);
      setActiveProject(newProject);
      await onProjectCreated();
      setOpenDialog(false);
      form.reset();
      toast.success("Project created successfully");
      router.push("/apps");
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Failed to create project");
      }
    } finally {
      setIsCreating(false);
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
                      disabled={isCreating}
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
                disabled={isCreating}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
