"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { SubmitHandler, useForm } from "react-hook-form";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
// import { MultiSelect } from "@/components/ui/multi-select"; // Import MultiSelect component
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";
import { AppConfig } from "@/lib/types/appconfig";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { RowSelectionState } from "@tanstack/react-table";
import { createColumnHelper, type ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { IdDisplay } from "@/components/apps/id-display";

const columnHelper = createColumnHelper<AppConfig>();
const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().min(1, "Description is required"),
  allowed_apps: z.array(z.string()).default([]),
  custom_instructions: z
    .record(z.string())
    .refine((obj) => Object.keys(obj).every((key) => typeof key === "string"), {
      message: "All keys must be strings.",
    })
    .refine(
      (obj) => Object.values(obj).every((value) => typeof value === "string"),
      {
        message: "All values must be strings.",
      },
    )
    .default({}),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateAgentFormProps {
  children: React.ReactNode;
  onSubmit: (values: FormValues) => Promise<void>;
  initialValues?: Partial<FormValues>;
  title: string;
  validAppNames: string[];
  appConfigs?: AppConfig[];
}

export function CreateAgentForm({
  children,
  onSubmit,
  initialValues,
  title,
  validAppNames,
  appConfigs = [],
}: CreateAgentFormProps) {
  const [open, setOpen] = useState(false);
  const [selectedApps, setSelectedApps] = useState<RowSelectionState>({});

  const columns: ColumnDef<AppConfig>[] = useMemo(() => {
    return [
      columnHelper.accessor("app_name", {
        header: ({ column }) => (
          <div className="text-left">
            <Button
              variant="ghost"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                column.toggleSorting(column.getIsSorted() === "asc");
              }}
              className="justify-start px-0"
              type="button"
            >
              App Name
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        ),
        cell: ({ row }) => <IdDisplay id={row.original.app_name} />,
        enableGlobalFilter: true,
        id: "app_name",
      }),
    ] as ColumnDef<AppConfig>[];
  }, []);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: initialValues?.name ?? "",
      description: initialValues?.description ?? "",
      allowed_apps: initialValues?.allowed_apps ?? [],
      custom_instructions: initialValues?.custom_instructions ?? {},
    },
  });

  const handleSubmit: SubmitHandler<FormValues> = async (values) => {
    try {
      // Validate custom_instructions keys against validAppNames
      const invalidKeys = Object.keys(values.custom_instructions).filter(
        (key) => !validAppNames.includes(key),
      );

      if (invalidKeys.length > 0) {
        form.setError("custom_instructions", {
          type: "manual",
          message: `Invalid app names in custom instructions: ${invalidKeys.join(", ")}. Must be one of: ${validAppNames.join(", ")}`,
        });
        return;
      }
      const appNames: string[] = Object.keys(selectedApps).filter(
        (app_name) => selectedApps[app_name],
      );
      values.allowed_apps = appNames;
      await onSubmit(values);
      setOpen(false);
      toast.success("Agent created successfully");
      form.reset();
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  };

  // Reset form values when dialog opens
  useEffect(() => {
    if (open) {
      form.reset({
        name: initialValues?.name ?? "",
        description: initialValues?.description ?? "",
        allowed_apps: initialValues?.allowed_apps ?? [],
        custom_instructions: initialValues?.custom_instructions ?? {},
      });
    }
    if (!open || appConfigs.length === 0) return;
    const allSelected: RowSelectionState = {};
    appConfigs.forEach((cfg) => {
      allSelected[cfg.app_name] = true;
    });
    setSelectedApps(allSelected);
    form.setValue("allowed_apps", Object.keys(allSelected));
  }, [open, initialValues, form, appConfigs]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
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
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium">Allowed Apps</h3>
                <Badge
                  variant="secondary"
                  className="flex items-center gap-1 px-2 py-1 text-xs"
                >
                  {Object.keys(selectedApps).length} selected
                </Badge>
              </div>
              {appConfigs.length === 0 ? (
                <div className="h-32 flex items-center justify-center">
                  <p>No available app configs</p>
                </div>
              ) : (
                <div className="max-h-[40vh] overflow-y-auto">
                  <EnhancedDataTable
                    columns={columns}
                    data={appConfigs}
                    defaultSorting={[{ id: "app_name", desc: true }]}
                    searchBarProps={{ placeholder: "Search apps..." }}
                    rowSelectionProps={{
                      rowSelection: selectedApps,
                      onRowSelectionChange: setSelectedApps,
                      getRowId: (row) => row.app_name,
                    }}
                  />
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="submit">Save</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
