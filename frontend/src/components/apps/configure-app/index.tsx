import { useEffect, useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

// import sub components
import { Stepper } from "@/components/apps/configure-app/stepper";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";

import { ConfigureAppStep } from "@/components/apps/configure-app/configure-app-step";
import { AgentSelectionStep } from "@/components/apps/configure-app/agent-selection-step";
import { LinkedAccountStep } from "@/components/apps/configure-app/linked-account-step";

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
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const [security_scheme, setSelectedSecurityScheme] = useState<string>("");

  const resetAll = useCallback(() => {
    setCurrentStep(1);
    setSelectedSecurityScheme("");
  }, []);

  useEffect(() => {
    if (!open) {
      resetAll();
    }
  }, [open, resetAll]);

  // step navigation handlers
  const handleConfigureAppNext = (selectedSecurityScheme: string) => {
    setSelectedSecurityScheme(selectedSecurityScheme);
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
        <div className="max-h-[70vh] overflow-y-auto p-1">
          {currentStep === 1 && (
            <ConfigureAppStep
              supported_security_schemes={supported_security_schemes}
              onNext={handleConfigureAppNext}
              name={name}
            />
          )}

          {currentStep === 2 && (
            <AgentSelectionStep
              onNext={handleAgentSelectionNext}
              appName={name}
              isDialogOpen={open}
            />
          )}

          {currentStep === 3 && (
            <LinkedAccountStep
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
