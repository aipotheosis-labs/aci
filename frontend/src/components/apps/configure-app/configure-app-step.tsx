import { useForm } from "react-hook-form";
import * as z from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { useState, useEffect } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { BsQuestionCircle, BsAsterisk } from "react-icons/bs";
import { Badge } from "@/components/ui/badge";
import { IdDisplay } from "@/components/apps/id-display";
import { Checkbox } from "@/components/ui/checkbox";
import { useCreateAppConfig } from "@/hooks/use-app-config";
import { toast } from "sonner";
import { AppAlreadyConfiguredError } from "@/lib/api/appconfig";

export const ConfigureAppFormSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
  client_id: z.string().optional().default(""),
  client_secret: z.string().optional().default(""),
  redirect_url: z
    .string()
    .optional()
    .default("")
    .transform((value) => value.trim())
    .refine(
      (value) => {
        if (!value) return true; // Empty is valid (optional field)
        try {
          const url = new URL(value);
          return url.protocol === "http:" || url.protocol === "https:";
        } catch {
          return false;
        }
      },
      {
        message: "Please enter a valid URL starting with http:// or https://",
      },
    )
    .refine(
      (value) => {
        if (!value) return true;
        return value !== defaultRedirectUrl;
      },
      // to catch likely user error
      {
        message:
          "Custom redirect URL cannot be the same as ACI.dev's redirect URL",
      },
    ),
});
export type ConfigureAppFormValues = z.infer<typeof ConfigureAppFormSchema>;
const defaultRedirectUrl = `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/oauth2/callback`;

interface ConfigureAppStepProps {
  supported_security_schemes: Record<string, { scope?: string }>;
  onNext: (securityScheme: string) => void;
  name: string;
}

export function ConfigureAppStep({
  supported_security_schemes,
  onNext,
  name,
}: ConfigureAppStepProps) {
  const {
    mutateAsync: createAppConfigMutation,
    isPending: isCreatingAppConfig,
  } = useCreateAppConfig();

  const form = useForm<ConfigureAppFormValues>({
    resolver: zodResolver(ConfigureAppFormSchema),
    defaultValues: {
      security_scheme: Object.keys(supported_security_schemes || {})[0],
      client_id: "",
      client_secret: "",
      redirect_url: "",
    },
  });

  const currentSecurityScheme = form.watch("security_scheme");
  const { scope = "" } =
    supported_security_schemes?.[currentSecurityScheme] ?? {};
  const scopes = scope.split(/[\s,]+/).filter(Boolean);

  const [useACIDevOAuth2, setUseACIDevOAuth2] = useState(false);
  const clientId = form.watch("client_id");
  const clientSecret = form.watch("client_secret");
  const redirectUrl = form.watch("redirect_url");

  const [isRedirectUrlAdditionConfirmed, setIsRedirectUrlAdditionConfirmed] =
    useState(false);
  const [
    isRedirectUrlForwardingConfirmed,
    setIsRedirectUrlForwardingConfirmed,
  ] = useState(false);
  const [isScopeConfirmed, setIsScopeConfirmed] = useState(false);

  // Determine which redirect URL to display - if custom is provided, show it, otherwise show default
  const effectiveRedirectUrl = redirectUrl || defaultRedirectUrl;
  const isUsingCustomRedirectUrl = !!redirectUrl;

  const isFormValid = () => {
    if (currentSecurityScheme === "oauth2" && !useACIDevOAuth2) {
      const redirectUrlConfirmed = isUsingCustomRedirectUrl
        ? isRedirectUrlAdditionConfirmed && isRedirectUrlForwardingConfirmed
        : isRedirectUrlAdditionConfirmed;

      return (
        !!clientId && !!clientSecret && redirectUrlConfirmed && isScopeConfirmed
      );
    }
    return true;
  };

  // listen to security_scheme changes, reset form state when needed
  useEffect(() => {
    if (currentSecurityScheme !== "oauth2") {
      form.setValue("client_id", "");
      form.setValue("client_secret", "");
      form.setValue("redirect_url", "");
      setUseACIDevOAuth2(false);
      setIsRedirectUrlAdditionConfirmed(false);
      setIsRedirectUrlForwardingConfirmed(false);
      setIsScopeConfirmed(false);
    }
  }, [currentSecurityScheme, form]);

  const handleSubmit = async (values: ConfigureAppFormValues) => {
    if (values.security_scheme === "oauth2" && !useACIDevOAuth2) {
      if (!values.client_id || !values.client_secret) {
        form.setError("client_id", {
          type: "manual",
          message: "Client ID is required for custom OAuth2",
        });
        form.setError("client_secret", {
          type: "manual",
          message: "Client Secret is required for custom OAuth2",
        });
        return;
      }
    }

    try {
      let security_scheme_overrides = undefined;

      if (
        values.security_scheme === "oauth2" &&
        !useACIDevOAuth2 &&
        !!values.client_id &&
        !!values.client_secret
      ) {
        security_scheme_overrides = {
          oauth2: {
            client_id: values.client_id,
            client_secret: values.client_secret,
            ...(values.redirect_url && {
              redirect_url: values.redirect_url,
            }),
          },
        };
      }

      await createAppConfigMutation({
        app_name: name,
        security_scheme: values.security_scheme,
        security_scheme_overrides,
      });

      toast.success(`Successfully configured app: ${name}`);
      onNext(values.security_scheme);
    } catch (error) {
      if (error instanceof AppAlreadyConfiguredError) {
        toast.error(`App configuration already exists for app: ${name}`);
      } else {
        console.error("Error configuring app:", error);
        toast.error(`Failed to configure app. Please try again.`);
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="mb-1">
        <div className="text-sm font-medium mb-2">API Provider</div>
        <div className="p-2 border rounded-md bg-muted/30 flex items-center gap-3">
          <span className="font-medium">{name}</span>
        </div>
      </div>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="security_scheme"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Authentication Method</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Supported Auth Type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {Object.entries(supported_security_schemes || {}).map(
                      ([scheme], idx) => (
                        <SelectItem key={idx} value={scheme}>
                          {scheme}
                        </SelectItem>
                      ),
                    )}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          {currentSecurityScheme === "oauth2" && (
            <div className="flex items-center gap-2">
              <Switch
                checked={useACIDevOAuth2}
                onCheckedChange={setUseACIDevOAuth2}
              />
              <Label className="text-sm font-medium">
                Use ACI.dev&apos;s OAuth2 App
              </Label>
            </div>
          )}

          {currentSecurityScheme === "oauth2" && !useACIDevOAuth2 && (
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="space-y-6 min-w-0">
                <FormField
                  control={form.control}
                  name="client_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1">
                        OAuth2 Client ID
                        <BsAsterisk className="h-2 w-2 text-red-500" />
                      </FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Client ID" required />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="client_secret"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1">
                        OAuth2 Client Secret
                        <BsAsterisk className="h-2 w-2 text-red-500" />
                      </FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          placeholder="Client Secret"
                          required
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Custom Redirect URL Option */}
                <FormField
                  control={form.control}
                  name="redirect_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="flex items-center gap-1">
                        Custom Redirect URL
                        <span className="text-xs text-muted-foreground font-normal">
                          (Optional)
                        </span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <BsQuestionCircle className="h-4 w-4 text-muted-foreground cursor-pointer" />
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            {`Leave empty to use ACI.dev's default.
                            For complete whitelabeling, provide your own redirect URL. In this case, your backend should forward
                            the OAuth2 callback response to ACI.dev's redirect URL.`}
                          </TooltipContent>
                        </Tooltip>
                      </FormLabel>
                      <FormControl>
                        <Input {...field} placeholder={defaultRedirectUrl} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* right column: read-only information */}
              <div className="space-y-6 min-w-0">
                {/* Redirect URL */}
                <FormItem>
                  <FormLabel className="flex items-center gap-1">
                    Redirect URL
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground cursor-pointer" />
                      </TooltipTrigger>
                      <TooltipContent>
                        Redirect URL is the URL to which the OAuth2 callback
                        response will be sent.
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>

                  <div className="pt-2">
                    <IdDisplay id={effectiveRedirectUrl} />
                  </div>
                  <div className="flex items-center gap-1">
                    <Checkbox
                      checked={isRedirectUrlAdditionConfirmed}
                      onCheckedChange={(checked) =>
                        setIsRedirectUrlAdditionConfirmed(checked === true)
                      }
                    />
                    <BsAsterisk className="h-2 w-2 text-red-500" />
                    <span className="text-xs">
                      I have added the above redirect URL to my OAuth2 app.
                    </span>
                  </div>

                  {isUsingCustomRedirectUrl && (
                    <div>
                      <div className="pt-1">
                        <IdDisplay id={defaultRedirectUrl} />
                      </div>
                      <div className="flex items-center gap-1 mt-2">
                        <Checkbox
                          checked={isRedirectUrlForwardingConfirmed}
                          onCheckedChange={(checked) =>
                            setIsRedirectUrlForwardingConfirmed(
                              checked === true,
                            )
                          }
                        />
                        <BsAsterisk className="h-2 w-2 text-red-500" />
                        <span className="text-xs">
                          I have set up my custom redirect URL to forward OAuth2
                          callback responses to above redirect URL.
                        </span>
                      </div>
                    </div>
                  )}
                </FormItem>

                {/* Scope */}
                <FormItem>
                  <FormLabel className="flex items-center gap-1">
                    Scope
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground cursor-pointer" />
                      </TooltipTrigger>
                      <TooltipContent>
                        Enter/Tick the scopes exactly as shown below in your
                        OAuth2 app settings. It defines the permissions your app
                        will request and must match for authentication to work
                        properly.
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto pt-2">
                    {scopes.map((s) => (
                      <Badge
                        key={s}
                        variant="secondary"
                        className="text-xs break-all"
                      >
                        <code className="break-all">{s}</code>
                      </Badge>
                    ))}
                  </div>
                  <div className="flex items-center gap-1">
                    <Checkbox
                      checked={isScopeConfirmed}
                      onCheckedChange={(checked) =>
                        setIsScopeConfirmed(checked === true)
                      }
                    />
                    <BsAsterisk className="h-2 w-2 text-red-500" />

                    <span className="text-xs">
                      I have added the above scopes to my OAuth2 app.
                    </span>
                  </div>
                </FormItem>
              </div>
            </div>
          )}

          {currentSecurityScheme === "oauth2" && useACIDevOAuth2 && (
            <div className="bg-yellow-100 border border-yellow-300 p-3 rounded flex items-start gap-2">
              {/* <BsQuestionCircle className="mt-1 h-4 w-4 text-yellow-700" /> */}
              <p className="text-sm text-yellow-900">
                We <strong>recommend</strong> using your own OAuth2 app in
                production.
                {/* <a
                  href="https://www.aci.dev/docs/core-concepts/linked-account#linking-oauth2-account"
                  target="_blank"
                  className="underline text-blue-700"
                >
                  See documentation →
                </a> */}
              </p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="submit"
              disabled={isCreatingAppConfig || !isFormValid()}
            >
              {isCreatingAppConfig ? "Confirming..." : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </div>
  );
}
