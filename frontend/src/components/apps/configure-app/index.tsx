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
import { toast } from "sonner";
import { RowSelectionState } from "@tanstack/react-table";
import { Agent } from "@/lib/types/project";
import { useMetaInfo } from "@/components/context/metainfo";
import { updateAgent } from "@/lib/api/agent";
import { getApiKey } from "@/lib/api/util";
import {
  createAPILinkedAccount,
  createNoAuthLinkedAccount,
  getOauth2LinkURL,
} from "@/lib/api/linkedaccount";

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
  FORM_SUBMIT_COPY_OAUTH2_LINK_URL,
  FORM_SUBMIT_LINK_OAUTH2_ACCOUNT,
  FORM_SUBMIT_API_KEY,
  FORM_SUBMIT_NO_AUTH,
} from "@/components/apps/configure-app/linked-account-step";

// step definitions
const STEPS = [
  { id: 1, title: "Configure App" },
  { id: 2, title: "Select Agents" },
  { id: 3, title: "Add Linked Account" },
];

interface ConfigureAppProps {
  children: React.ReactNode;
  configureApp: (
    security_scheme: string,
    security_scheme_overrides?: {
      oauth2?: {
        client_id: string;
        client_secret: string;
      } | null;
    },
  ) => Promise<boolean>;
  name: string;
  supported_security_schemes: Record<string, { scope?: string }>;
  logo?: string;
}

export function ConfigureApp({
  children,
  configureApp,
  name,
  supported_security_schemes,
  logo,
}: ConfigureAppProps) {
  const { activeProject, reloadActiveProject, accessToken } = useMetaInfo();
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedAgentIds, setSelectedAgentIds] = useState<RowSelectionState>(
    {},
  );
  const [submitLoading, setSubmitLoading] = useState(false);

  // security scheme
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

  // step 1 submit
  const handleConfigureAppSubmit = async (values: ConfigureAppFormValues) => {
    setSelectedSecurityScheme(values.security_scheme);
    setSubmitLoading(true);

    try {
      let security_scheme_overrides = undefined;

      if (
        values.security_scheme === "oauth2" &&
        values.client_id &&
        values.client_secret
      ) {
        security_scheme_overrides = {
          oauth2: {
            client_id: values.client_id,
            client_secret: values.client_secret,
          },
        };
      }

      const success = await configureApp(
        values.security_scheme,
        security_scheme_overrides,
      );
      if (success) {
        setCurrentStep(2);
      }
    } catch (error) {
      console.error("Failed to configure app:", error);
      toast.error("Failed to configure app. Please try again.");
    } finally {
      setSubmitLoading(false);
    }
  };

  // step 2 submit
  const handleAgentSelectionSubmit = async () => {
    if (Object.keys(selectedAgentIds).length === 0) {
      setCurrentStep(3);
      return;
    }

    try {
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
      toast.success("agents updated successfully");
      await reloadActiveProject();
      setCurrentStep(3);
    } catch (error) {
      console.error("agents updated app failed:", error);
      toast.error("agents updated app failed");
    }
  };

  // step 3 submit -  handle account linking
  const handleLinkedAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nativeEvent = e.nativeEvent as SubmitEvent;
    const submitter = nativeEvent.submitter as HTMLButtonElement;
    if (submitter.name == "skip") {
      setOpen(false);
      return;
    }

    try {
      setSubmitLoading(true);

      // Set auth type for form validation
      linkedAccountForm.setValue("_authType", security_scheme);

      // validate form
      await linkedAccountForm.trigger();
      if (!linkedAccountForm.formState.isValid) {
        setSubmitLoading(false);
        return;
      }

      const values = linkedAccountForm.getValues();

      // handle different actions based on submit button
      switch (submitter.name) {
        case FORM_SUBMIT_COPY_OAUTH2_LINK_URL:
          await copyOAuth2LinkURL(name, values.linkedAccountOwnerId);
          break;
        case FORM_SUBMIT_LINK_OAUTH2_ACCOUNT:
          await linkOauth2Account(name, values.linkedAccountOwnerId);
          break;
        case FORM_SUBMIT_API_KEY:
          await linkAPIAccount(
            name,
            values.linkedAccountOwnerId,
            values.apiKey as string,
          );
          break;
        case FORM_SUBMIT_NO_AUTH:
          await linkNoAuthAccount(name, values.linkedAccountOwnerId);
          break;
      }

      setOpen(false);
    } catch (error) {
      console.error("Error adding linked account:", error);
      toast.error("add linked account failed");
    } finally {
      setSubmitLoading(false);
    }
  };

  // fetch oauth2 link url
  const fetchOAuth2LinkURL = async (
    appName: string,
    linkedAccountOwnerId: string,
    afterOAuth2LinkRedirectURL?: string,
  ): Promise<string> => {
    if (!appName) {
      throw new Error("no app selected");
    }

    const apiKey = getApiKey(activeProject);

    if (afterOAuth2LinkRedirectURL === undefined) {
      return await getOauth2LinkURL(appName, linkedAccountOwnerId, apiKey);
    } else {
      return await getOauth2LinkURL(
        appName,
        linkedAccountOwnerId,
        apiKey,
        afterOAuth2LinkRedirectURL,
      );
    }
  };

  const copyOAuth2LinkURL = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    try {
      const url = await fetchOAuth2LinkURL(appName, linkedAccountOwnerId);
      if (!navigator.clipboard) {
        console.error("Clipboard API not supported");
        toast.error("your browser does not support copy to clipboard");
        return;
      }
      navigator.clipboard
        .writeText(url)
        .then(() => {
          toast.success("OAuth2 link URL copied to clipboard");
        })
        .catch((err) => {
          console.error("Failed to copy:", err);
          toast.error(
            "copy OAuth2 link URL to clipboard failed, please start OAuth2 Flow",
          );
        });
    } catch (error) {
      console.error(error);
      toast.error(
        "copy OAuth2 link URL to clipboard failed, please start OAuth2 Flow",
      );
    }
  };

  const linkOauth2Account = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    if (!appName) {
      toast.error("no app selected");
      return;
    }

    try {
      const oauth2LinkURL = await fetchOAuth2LinkURL(
        appName,
        linkedAccountOwnerId,
        `${process.env.NEXT_PUBLIC_DEV_PORTAL_URL}/appconfigs/${appName}`,
      );
      window.location.href = oauth2LinkURL;
    } catch (error) {
      console.error("Error linking OAuth2 account:", error);
      toast.error("link account failed");
    }
  };

  const linkAPIAccount = async (
    appName: string,
    linkedAccountOwnerId: string,
    linkedAPIKey: string,
  ) => {
    if (!appName) {
      throw new Error("no app selected");
    }

    const apiKey = getApiKey(activeProject);

    try {
      await createAPILinkedAccount(
        appName,
        linkedAccountOwnerId,
        linkedAPIKey,
        apiKey,
      );
      toast.success("account linked successfully");
    } catch (error) {
      console.error("Error linking API account:", error);
      toast.error("link account failed");
    }
  };

  const linkNoAuthAccount = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    if (!appName) {
      throw new Error("no app selected");
    }

    const apiKey = getApiKey(activeProject);

    try {
      await createNoAuthLinkedAccount(appName, linkedAccountOwnerId, apiKey);
      toast.success("account linked successfully");
    } catch (error) {
      console.error("Error linking no auth account:", error);
      toast.error("link account failed");
    }
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
          {/* <DialogDescription>Add an app to your project</DialogDescription> */}
        </DialogHeader>

        {/* stepper */}
        <Stepper currentStep={currentStep} totalSteps={3} steps={STEPS} />

        {/* step content */}
        <div className="max-h-[50vh] overflow-y-auto p-1">
          {currentStep === 1 && (
            <ConfigureAppStep
              form={ConfigureAppForm}
              supported_security_schemes={supported_security_schemes}
              onNext={handleConfigureAppSubmit}
              name={name}
              isLoading={submitLoading}
            />
          )}

          {currentStep === 2 && (
            <AgentSelectionStep
              agents={activeProject.agents}
              rowSelection={selectedAgentIds}
              onRowSelectionChange={setSelectedAgentIds}
              onNext={handleAgentSelectionSubmit}
              isLoading={submitLoading}
            />
          )}

          {currentStep === 3 && (
            <LinkedAccountStep
              form={linkedAccountForm}
              authType={security_scheme}
              onSubmit={handleLinkedAccountSubmit}
              isLoading={submitLoading}
              setCurrentStep={setCurrentStep}
              onClose={() => setOpen(false)}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
