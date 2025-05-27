import { useEffect, useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { RowSelectionState } from "@tanstack/react-table";
import { Agent } from "@/lib/types/project";
import { useMetaInfo } from "@/components/context/metainfo";

// import sub components
import { Stepper } from "@/components/apps/configure-app/stepper";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";

import {
  ConfigureAppStep,
  ConfigureAppFormValues,
  ConfigureAppFormSchema,
} from "@/components/apps/configure-app/configure-app-step";
import {
  AgentSelectionStep,
  AgentSelectFormValues,
  agentSelectFormSchema,
} from "@/components/apps/configure-app/agent-selection-step";
import {
  LinkedAccountStep,
  LinkedAccountFormValues,
  linkedAccountFormSchema,
} from "@/components/apps/configure-app/linked-account-step";

// step definitions
const STEPS = [
  { id: 1, title: "Configure App" },
  { id: 2, title: "Select Agents" },
  { id: 3, title: "Add Linked Account" },
];

interface ConfigureAppProps {
  children: React.ReactNode;
  name: string;
  supported_security_schemes: Record<string, { scope?: string }>;
  logo?: string;
}

export function ConfigureApp({
  children,
  name,
  supported_security_schemes,
  logo,
}: ConfigureAppProps) {
  const { activeProject } = useMetaInfo();
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedAgentIds, setSelectedAgentIds] = useState<RowSelectionState>(
    {},
  );
  const [security_scheme, setSelectedSecurityScheme] = useState<string>("");

  // security scheme form
  const ConfigureAppForm = useForm<ConfigureAppFormValues>({
    resolver: zodResolver(ConfigureAppFormSchema),
    defaultValues: {
      security_scheme: Object.keys(supported_security_schemes || {})[0],
      client_id: "",
      client_secret: "",
    },
  });

  const agentSelectForm = useForm<AgentSelectFormValues>({
    resolver: zodResolver(agentSelectFormSchema),
    defaultValues: {
      agents: [],
    },
  });

  const linkedAccountForm = useForm<LinkedAccountFormValues>({
    resolver: zodResolver(linkedAccountFormSchema),
    defaultValues: {
      linkedAccountOwnerId: "",
      apiKey: "",
    },
  });

  // reset all form and state
  const resetAll = useCallback(() => {
    setCurrentStep(1);
    setSelectedAgentIds({});
    setSelectedSecurityScheme("");
    ConfigureAppForm.reset();
    agentSelectForm.reset();
    linkedAccountForm.reset();
  }, [ConfigureAppForm, agentSelectForm, linkedAccountForm]);

  useEffect(() => {
    if (!open) {
      resetAll();
    }
  }, [open, resetAll]);

  useEffect(() => {
    if (open && activeProject?.agents) {
      const initialSelection: RowSelectionState = {};
      activeProject.agents.forEach((agent: Agent) => {
        if (agent.id) {
          initialSelection[agent.id] = true;
        }
      });
      setSelectedAgentIds(initialSelection);
    }
  }, [open, activeProject]);

  // step navigation handlers
  const handleConfigureAppNext = () => {
    const currentSecurityScheme = ConfigureAppForm.getValues("security_scheme");
    setSelectedSecurityScheme(currentSecurityScheme);
    setCurrentStep(2);
  };

  const handleAgentSelectionNext = () => {
    setCurrentStep(3);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[65vw]">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold flex items-center gap-2">
            Configure App
            <Badge variant="secondary" className="p-2">
              <Image
                src={logo ?? ""}
                alt={`${name} logo`}
                width={20}
                height={20}
                className="object-contain mr-1"
              />
              {name}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {/* stepper */}
        <Stepper currentStep={currentStep} totalSteps={3} steps={STEPS} />

        {/* step content */}
        <div className="max-h-[50vh] overflow-y-auto p-1">
          {currentStep === 1 && (
            <ConfigureAppStep
              form={ConfigureAppForm}
              supported_security_schemes={supported_security_schemes}
              onNext={handleConfigureAppNext}
              name={name}
            />
          )}

          {currentStep === 2 && (
            <AgentSelectionStep
              agents={activeProject.agents}
              rowSelection={selectedAgentIds}
              onRowSelectionChange={setSelectedAgentIds}
              onNext={handleAgentSelectionNext}
              appName={name}
            />
          )}

          {currentStep === 3 && (
            <LinkedAccountStep
              form={linkedAccountForm}
              authType={security_scheme}
              onClose={handleClose}
              appName={name}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
