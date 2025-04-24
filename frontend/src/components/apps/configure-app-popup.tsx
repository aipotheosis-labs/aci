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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Agent } from "@/lib/types/project";
import { useAgentColumns } from "@/components/apps/useAgentColumns";
import { EnhancedDataTable } from "@/components/ui-extensions/enhanced-data-table/data-table";
import { updateAgent } from "@/lib/api/agent";
import { toast } from "sonner";
import { useMetaInfo } from "@/components/context/metainfo";

const formSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
});

type FormValues = z.infer<typeof formSchema>;

interface ConfigureAppPopupProps {
  children: React.ReactNode;
  configureApp: (security_scheme: string) => Promise<void>;
  name: string;
  security_schemes: string[];
}

export function ConfigureAppPopup({
  children,
  configureApp,
  name,
  security_schemes,
}: ConfigureAppPopupProps) {
  const { activeProject, reloadActiveProject, accessToken } = useMetaInfo();

  const [open, setOpen] = useState(false);
  const [selectedAgentIds, setSelectedAgentIds] = useState<
    Record<string, boolean>
  >({});

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      security_scheme: security_schemes?.[0] ?? "",
    },
  });

  useEffect(() => {
    if (!open) {
      setSelectedAgentIds({});
      form.reset();
    }
  }, [open, form]);

  useEffect(() => {
    if (open && activeProject?.agents) {
      const initialSelection: Record<string, boolean> = {};
      activeProject.agents.forEach((agent: Agent) => {
        if (agent.id) {
          initialSelection[agent.id] = true;
        }
      });
      setSelectedAgentIds(initialSelection);
    }
  }, [open, activeProject]);

  const handleSubmit: SubmitHandler<FormValues> = async (values) => {
    try {
      await configureApp(values.security_scheme);

      const agentsToUpdate = activeProject.agents.filter(
        (agent) => agent.id && selectedAgentIds[agent.id],
      );

      for (const agent of agentsToUpdate) {
        const allowedApps = new Set(agent.allowed_apps);
        allowedApps.add(name);
        await updateAgent(
          activeProject.id,
          agent.id,
          accessToken,
          undefined,
          undefined,
          Array.from(allowedApps),
        );
      }

      try {
        await reloadActiveProject();
      } catch (error) {
        console.error("Failed to reload project data:", error);
        toast.error("Changes saved, but failed to refresh data");
      }
      setOpen(false);
    } catch (error) {
      console.error("Error submitting form:", error);
      toast.error("Error configuring app");
    }
  };

  const toggleAgentSelection = (agentId: string) => {
    setSelectedAgentIds((prev) => ({
      ...prev,
      [agentId]: !prev[agentId],
    }));
  };

  const agentColumns = useAgentColumns(selectedAgentIds, toggleAgentSelection);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Configure App</DialogTitle>
          <p className="text-sm text-gray-500 mt-2">
            Add an app to your project
          </p>
        </DialogHeader>

        <div className="mb-4">
          <div className="text-sm">API Provider</div>
          <div className="p-2 border rounded bg-gray-100">{name}</div>
        </div>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="security_scheme"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Supported Auth Type</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select Auth Type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {security_schemes.map((scheme, index) => (
                        <SelectItem key={index} value={scheme}>
                          {scheme}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {activeProject.agents.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">
                  Select Agents to enable this app
                </h3>
                <EnhancedDataTable
                  columns={agentColumns}
                  data={activeProject.agents}
                  searchBarProps={{ placeholder: "Search Agent..." }}
                />
              </div>
            )}

            <DialogFooter>
              <Button type="submit">Save</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
