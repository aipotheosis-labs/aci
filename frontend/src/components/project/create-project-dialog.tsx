"use client";

import { useState } from "react";
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
  DialogTrigger,
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

const formSchema = z.object({
  name: z.string().min(1, "Project name cannot be empty"),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateProjectDialogProps {
  accessToken: string;
  orgId: string;
  onProjectCreated: () => Promise<void>;
  trigger?: React.ReactNode;
  openDialog?: boolean;
  setOpenDialog?: (open: boolean) => void;
}

export function CreateProjectDialog({
  accessToken,
  orgId,
  onProjectCreated,
  trigger,
  openDialog,
  setOpenDialog,
}: CreateProjectDialogProps) {
  const [open, setOpen] = useState(false);
  const { setActiveProject } = useMetaInfo();
  const router = useRouter();

  // Use controlled open state if provided
  const isOpen = openDialog !== undefined ? openDialog : open;
  const setIsOpen = setOpenDialog || setOpen;

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
    },
  });

  const handleSubmit = async (values: FormValues) => {
    try {
      const newProject = await createProject(accessToken, values.name, orgId);
      console.log("newProject", newProject);
      setActiveProject(newProject);
      await onProjectCreated();
      setIsOpen(false);
      form.reset();
      toast.success("Project created successfully");
      router.push("/apps");
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      console.log("error", error);
      toast.error(error.message || "Failed to create project");
    }
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) {
          form.reset();
        }
      }}
    >
      <DialogTrigger asChild>
        {trigger || <Button>Create Project</Button>}
      </DialogTrigger>
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
                    <Input placeholder="Enter project name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit">Create</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
