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
  form: ReturnType<typeof useForm<LinkedAccountFormValues>>;
  authType: string;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  isLoading: boolean;
  setCurrentStep: (step: number) => void;
  onClose: () => void;
}

export function LinkedAccountStep({
  form,
  authType,
  onSubmit,
  isLoading,
  onClose,
}: LinkedAccountStepProps) {
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <h3 className="text-lg font-medium">Add Linked Account</h3>
      </div>

      <FormProvider {...form}>
        <form onSubmit={onSubmit} className="space-y-4">
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
                  disabled={isLoading}
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
