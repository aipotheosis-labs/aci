import { useForm, FormProvider } from "react-hook-form";
import * as z from "zod";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import Link from "next/link";
import { BsQuestionCircle } from "react-icons/bs";
import { MdDescription } from "react-icons/md";
import { GoCopy } from "react-icons/go";
import {
  useCreateAPILinkedAccount,
  useCreateNoAuthLinkedAccount,
  useGetOauth2LinkURL,
} from "@/hooks/use-linked-account";
import { toast } from "sonner";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";

// Form submission types constants
export const FORM_SUBMIT_COPY_OAUTH2_LINK_URL = "copyOAuth2LinkURL";
export const FORM_SUBMIT_LINK_OAUTH2_ACCOUNT = "linkOAuth2";
export const FORM_SUBMIT_API_KEY = "apiKey";
export const FORM_SUBMIT_NO_AUTH = "noAuth";

// Form schema for linked account
export interface LinkedAccountFormValues {
  linkedAccountOwnerId: string;
  apiKey?: string;
  _authType?: string;
}

export const linkedAccountFormSchema = z
  .object({
    linkedAccountOwnerId: z.string().min(1, "Account owner ID is required"),
    apiKey: z.string().optional(),
    _authType: z.string().optional(),
  })
  .refine(
    (data) => {
      // if auth type is api_key, apiKey is required
      return (
        data._authType !== "api_key" || (data.apiKey && data.apiKey.length > 0)
      );
    },
    {
      message: "API Key is required",
      path: ["apiKey"],
    },
  );

interface LinkedAccountStepProps {
  authType: string;
  onClose: () => void;
  appName: string;
}

export function LinkedAccountStep({
  authType,
  onClose,
  appName,
}: LinkedAccountStepProps) {
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<LinkedAccountFormValues>({
    resolver: zodResolver(linkedAccountFormSchema),
    defaultValues: {
      linkedAccountOwnerId: "",
      apiKey: "",
    },
  });

  const {
    mutateAsync: createAPILinkedAccount,
    isPending: isCreatingAPILinkedAccount,
  } = useCreateAPILinkedAccount();
  const {
    mutateAsync: createNoAuthLinkedAccount,
    isPending: isCreatingNoAuthLinkedAccount,
  } = useCreateNoAuthLinkedAccount();
  const { mutateAsync: getOauth2LinkURL, isPending: isGettingOauth2LinkURL } =
    useGetOauth2LinkURL();

  const totalLoading =
    isLoading ||
    isCreatingAPILinkedAccount ||
    isCreatingNoAuthLinkedAccount ||
    isGettingOauth2LinkURL;

  // fetch oauth2 link url
  const fetchOAuth2LinkURL = async (
    linkedAccountOwnerId: string,
    afterOAuth2LinkRedirectURL?: string,
  ): Promise<string> => {
    if (!appName) {
      throw new Error("no app selected");
    }

    return await getOauth2LinkURL({
      appName,
      linkedAccountOwnerId,
      afterOAuth2LinkRedirectURL,
    });
  };

  const copyOAuth2LinkURL = async (linkedAccountOwnerId: string) => {
    try {
      const url = await fetchOAuth2LinkURL(linkedAccountOwnerId);
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

  const linkOauth2Account = async (linkedAccountOwnerId: string) => {
    if (!appName) {
      toast.error("no app selected");
      return;
    }

    try {
      const oauth2LinkURL = await fetchOAuth2LinkURL(
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
    linkedAccountOwnerId: string,
    linkedAPIKey: string,
  ) => {
    if (!appName) {
      throw new Error("no app selected");
    }

    try {
      await createAPILinkedAccount({
        appName,
        linkedAccountOwnerId,
        linkedAPIKey,
      });

      toast.success("account linked successfully");
      onClose();
    } catch (error) {
      console.error("Error linking API account:", error);
      toast.error("link account failed");
    }
  };

  const linkNoAuthAccount = async (linkedAccountOwnerId: string) => {
    if (!appName) {
      throw new Error("no app selected");
    }

    try {
      await createNoAuthLinkedAccount({
        appName,
        linkedAccountOwnerId,
      });

      toast.success("account linked successfully");
      onClose();
    } catch (error) {
      console.error("Error linking no auth account:", error);
      toast.error("link account failed");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const nativeEvent = e.nativeEvent as SubmitEvent;
    const submitter = nativeEvent.submitter as HTMLButtonElement;
    if (submitter.name == "skip") {
      onClose();
      return;
    }

    try {
      setIsLoading(true);

      // Set auth type for form validation
      form.setValue("_authType", authType);

      // validate form
      await form.trigger();
      if (!form.formState.isValid) {
        setIsLoading(false);
        return;
      }

      const values = form.getValues();

      // handle different actions based on submit button
      switch (submitter.name) {
        case FORM_SUBMIT_COPY_OAUTH2_LINK_URL:
          await copyOAuth2LinkURL(values.linkedAccountOwnerId);
          break;
        case FORM_SUBMIT_LINK_OAUTH2_ACCOUNT:
          await linkOauth2Account(values.linkedAccountOwnerId);
          break;
        case FORM_SUBMIT_API_KEY:
          await linkAPIAccount(
            values.linkedAccountOwnerId,
            values.apiKey as string,
          );
          break;
        case FORM_SUBMIT_NO_AUTH:
          await linkNoAuthAccount(values.linkedAccountOwnerId);
          break;
      }
    } catch (error) {
      console.error("Error adding linked account:", error);
      toast.error("add linked account failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <h3 className="text-lg font-medium">Add Linked Account</h3>
      </div>

      <FormProvider {...form}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            control={form.control}
            name="linkedAccountOwnerId"
            render={({ field }) => (
              <FormItem>
                <div className="flex items-center gap-2">
                  <FormLabel>linked account owner id</FormLabel>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="cursor-pointer">
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                      </span>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <p className="text-xs">
                        {"enter a name or label for your terminal users."}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Link
                        href={`https://www.aci.dev/docs/core-concepts/linked-account`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <MdDescription className="h-4 w-4 text-muted-foreground hover:text-primary" />
                      </Link>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <p className="text-xs">
                        {"learn more about linked account."}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </div>
                <FormControl>
                  <Input placeholder="linked account owner id" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {authType === "api_key" && (
            <FormField
              control={form.control}
              name="apiKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>API key</FormLabel>
                  <FormControl>
                    <Input placeholder="API key" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:gap-0">
            <div className="flex flex-row gap-2 w-full justify-end">
              <Button
                type="submit"
                name="skip"
                variant="outline"
                onClick={onClose}
              >
                Skip Add Account
              </Button>

              {authType === "oauth2" && (
                <Button
                  type="submit"
                  name={FORM_SUBMIT_COPY_OAUTH2_LINK_URL}
                  variant="outline"
                  className="flex items-center gap-2"
                  disabled={totalLoading}
                >
                  <GoCopy className="h-4 w-4" />
                  Copy OAuth2 URL
                </Button>
              )}

              {authType === "oauth2" && (
                <Button
                  type="submit"
                  name={FORM_SUBMIT_LINK_OAUTH2_ACCOUNT}
                  className="group relative flex items-center px-6 gap-2"
                  disabled={totalLoading}
                >
                  Start OAuth2 Flow
                </Button>
              )}

              {authType !== "oauth2" && (
                <Button
                  type="submit"
                  name={(() => {
                    switch (authType) {
                      case "no_auth":
                        return FORM_SUBMIT_NO_AUTH;
                      case "api_key":
                        return FORM_SUBMIT_API_KEY;
                      default:
                        return FORM_SUBMIT_NO_AUTH;
                    }
                  })()}
                  disabled={totalLoading}
                >
                  Save
                </Button>
              )}
            </div>
          </DialogFooter>
        </form>
      </FormProvider>
    </div>
  );
}
