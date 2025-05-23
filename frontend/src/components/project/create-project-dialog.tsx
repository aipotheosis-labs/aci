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

const formSchema = z.object({
  name: z.string().min(1, "Project name is required"),
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
      await createProject(accessToken, values.name, orgId);
      await onProjectCreated();
      setIsOpen(false);
      form.reset();
      toast.success("Project created successfully");
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      console.error("Failed to create project:", error);

      if (
        error.message?.includes("maximum projects quota") ||
        error.message?.includes("Max projects reached") ||
        error.message?.toLowerCase().includes("max projects")
      ) {
        toast.error(
          "You have reached the maximum number of projects allowed for your plan",
        );
      } else {
        toast.error("Failed to create project");
      }
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
                    <Input
                      placeholder="Enter project name"
                      {...field}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          form.handleSubmit(handleSubmit)();
                        }
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsOpen(false)}>
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
