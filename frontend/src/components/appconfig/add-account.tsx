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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BsQuestionCircle } from "react-icons/bs";
import { MdDescription } from "react-icons/md";
import Link from "next/link";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { GoCopy, GoPlus } from "react-icons/go";
import { toast } from "sonner";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useState } from "react";
import Image from "next/image";
import {
  useCreateAPILinkedAccount,
  useCreateNoAuthLinkedAccount,
  useGetOauth2LinkURL,
} from "@/hooks/use-linked-account";

const formSchema = z
  .object({
    appName: z.string().min(1, "App name is required"),
    authType: z.enum(["api_key", "oauth2", "no_auth"]),
    linkedAccountOwnerId: z.string().min(1, "Account owner ID is required"),
    apiKey: z.string().optional(),
  })
  .refine(
    (data) => {
      // If the current app uses api_key auth, then apiKey must be provided
      return (
        data.authType !== "api_key" || (data.apiKey && data.apiKey.length > 0)
      );
    },
    {
      message: "API Key is required",
      path: ["apiKey"],
    },
  );

type FormValues = z.infer<typeof formSchema>;

// Form submission types
const FORM_SUBMIT_COPY_OAUTH2_LINK_URL = "copyOAuth2LinkURL";
const FORM_SUBMIT_LINK_OAUTH2_ACCOUNT = "linkOAuth2";
const FORM_SUBMIT_API_KEY = "apiKey";
const FORM_SUBMIT_NO_AUTH = "noAuth";
export interface AppInfo {
  name: string;
  logo: string | undefined;
  supported_security_schemes: Record<string, { scope?: string }>;
}
interface AddAccountProps {
  appInfos: AppInfo[];
}

export function AddAccountForm({ appInfos }: AddAccountProps) {
  const [open, setOpen] = useState(false);

  const { mutateAsync: createApiLinkedAccount } = useCreateAPILinkedAccount();
  const { mutateAsync: createNoAuthLinkedAccount } =
    useCreateNoAuthLinkedAccount();
  const { mutateAsync: getOauth2URL } = useGetOauth2LinkURL();
  if (appInfos.length === 0) {
    console.error("No app infos provided");
    throw new Error("No app infos provided");
  }

  const appInfosDict = appInfos.reduce(
    (acc, appInfo) => {
      acc[appInfo.name] = appInfo;
      return acc;
    },
    {} as Record<string, AppInfo>,
  );

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      appName: appInfos[0].name,
      authType: Object.keys(appInfos[0].supported_security_schemes)[0] as
        | "api_key"
        | "oauth2"
        | "no_auth",
      linkedAccountOwnerId: "",
      apiKey: "",
    },
  });

  const selectedAppName = form.watch("appName");
  const selectedAuthType = form.watch("authType");

  const fetchOath2LinkURL = async (
    appName: string,
    linkedAccountOwnerId: string,
    afterOAuth2LinkRedirectURL?: string,
  ): Promise<string> => {
    if (!appName) {
      throw new Error("No app selected");
    }

    return await getOauth2URL({
      appName,
      linkedAccountOwnerId,
      afterOAuth2LinkRedirectURL,
    });
  };

  const copyOAuth2LinkURL = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    try {
      const url = await fetchOath2LinkURL(appName, linkedAccountOwnerId);
      if (!navigator.clipboard) {
        console.error("Clipboard API not supported");
        toast.error("Your browser doesn't support copying to clipboard");
        return;
      }
      navigator.clipboard
        .writeText(url)
        .then(() => {
          toast.success("OAuth2 link URL copied to clipboard");
        })
        .catch((err) => {
          console.error("Failed to copy:", err);
        });
    } catch (error) {
      console.error(error);
    }
  };

  const linkOauth2Account = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    if (!appName) {
      toast.error("No app selected");
      return;
    }

    try {
      const oauth2LinkURL = await fetchOath2LinkURL(
        appName,
        linkedAccountOwnerId,
        `${process.env.NEXT_PUBLIC_DEV_PORTAL_URL}/appconfigs/${appName}`,
      );
      window.location.href = oauth2LinkURL;
    } catch (error) {
      console.error("Error linking OAuth2 account:", error);
    }
  };

  const linkAPIAccount = async (
    appName: string,
    linkedAccountOwnerId: string,
    linkedAPIKey: string,
  ) => {
    if (!appName) {
      throw new Error("No app selected");
    }

    try {
      await createApiLinkedAccount({
        appName,
        linkedAccountOwnerId,
        linkedAPIKey,
      });

      toast.success("Account linked successfully");
      form.reset();
      setOpen(false);
    } catch (error) {
      console.error("Error linking API account:", error);
    }
  };

  const linkNoAuthAccount = async (
    appName: string,
    linkedAccountOwnerId: string,
  ) => {
    if (!appName) {
      throw new Error("No app selected");
    }

    try {
      await createNoAuthLinkedAccount({
        appName,
        linkedAccountOwnerId,
      });

      toast.success("Account linked successfully");
      form.reset();
      setOpen(false);
    } catch (error) {
      console.error("Error linking no auth account:", error);
    }
  };

  const onSubmit: SubmitHandler<FormValues> = async (values, e) => {
    if (!e) {
      throw new Error("Form submission event is not available");
    }

    const nativeEvent = e.nativeEvent as SubmitEvent;
    const submitter = nativeEvent.submitter as HTMLButtonElement;

    switch (submitter.name) {
      case FORM_SUBMIT_COPY_OAUTH2_LINK_URL:
        await copyOAuth2LinkURL(values.appName, values.linkedAccountOwnerId);
        break;
      case FORM_SUBMIT_LINK_OAUTH2_ACCOUNT:
        await linkOauth2Account(values.appName, values.linkedAccountOwnerId);
        break;
      case FORM_SUBMIT_API_KEY:
        await linkAPIAccount(
          values.appName,
          values.linkedAccountOwnerId,
          values.apiKey as string,
        );
        break;
      case FORM_SUBMIT_NO_AUTH:
        await linkNoAuthAccount(values.appName, values.linkedAccountOwnerId);
        break;
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        setOpen(open);
        form.reset();
      }}
    >
      <div className="flex items-center gap-2">
        <DialogTrigger asChild>
          <Button>
            <GoPlus />
            Add Account
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="cursor-pointer">
                  <BsQuestionCircle className="h-4 w-4 " />
                </span>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p className="text-xs">{"Add an end-user account."}</p>
              </TooltipContent>
            </Tooltip>
          </Button>
        </DialogTrigger>
      </div>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Account</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              form.handleSubmit(onSubmit)(e);
            }}
            className="grid gap-4 py-4"
          >
            <FormField
              control={form.control}
              name="appName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>App Name</FormLabel>
                  <Select
                    onValueChange={(value) => {
                      field.onChange(value);
                      form.setValue(
                        "authType",
                        Object.keys(
                          appInfosDict[value].supported_security_schemes,
                        )[0] as "api_key" | "oauth2" | "no_auth",
                        {
                          shouldValidate: true,
                        },
                      );
                    }}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select app" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {appInfos.map((appInfo) => (
                        <SelectItem key={appInfo.name} value={appInfo.name}>
                          <div className="flex items-center gap-2">
                            {appInfo.logo && (
                              <div className="relative h-5 w-5 flex-shrink-0 overflow-hidden">
                                <Image
                                  src={appInfo.logo}
                                  alt={appInfo.name}
                                  fill
                                  className="object-contain"
                                />
                              </div>
                            )}
                            {appInfo.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="linkedAccountOwnerId"
              render={({ field }) => (
                <FormItem>
                  <div className="flex items-center gap-2">
                    <FormLabel>Linked Account Owner ID</FormLabel>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="cursor-pointer">
                          <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p className="text-xs">
                          {"Input a name or label for your end user."}
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
                          {"Learn more about linked accounts."}
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

            <FormField
              control={form.control}
              name="authType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Auth Type</FormLabel>
                  <Select
                    onValueChange={(value) => {
                      if (value) {
                        field.onChange(value);
                      }
                    }}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select auth type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.keys(
                        appInfosDict[selectedAppName]
                          .supported_security_schemes,
                      ).map((scheme) => (
                        <SelectItem key={scheme} value={scheme}>
                          {scheme}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {selectedAuthType === "api_key" && (
              <FormField
                control={form.control}
                name="apiKey"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>API Key</FormLabel>
                    <FormControl>
                      <Input placeholder="api key" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setOpen(false)}
                type="button"
              >
                Cancel
              </Button>

              {selectedAuthType === "oauth2" && (
                <Button
                  type="submit"
                  name={FORM_SUBMIT_COPY_OAUTH2_LINK_URL}
                  variant={"outline"}
                >
                  <GoCopy />
                  Copy OAuth2 URL
                </Button>
              )}

              <Button
                type="submit"
                name={(() => {
                  switch (selectedAuthType) {
                    case "oauth2":
                      return FORM_SUBMIT_LINK_OAUTH2_ACCOUNT;
                    case "no_auth":
                      return FORM_SUBMIT_NO_AUTH;
                    case "api_key":
                      return FORM_SUBMIT_API_KEY;
                    default:
                      return FORM_SUBMIT_NO_AUTH;
                  }
                })()}
                disabled={!selectedAppName}
              >
                {selectedAuthType === "oauth2" ? "Start OAuth2 Flow" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
