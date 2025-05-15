import { useForm } from "react-hook-form";
import * as z from "zod";
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

export const ConfigureAppFormSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
  client_id: z.string().optional().default(""),
  client_secret: z.string().optional().default(""),
});
export type ConfigureAppFormValues = z.infer<typeof ConfigureAppFormSchema>;
const oauth2RedirectUrl = `${process.env.NEXT_PUBLIC_API_URL}/v1/linked-accounts/oauth2/callback`;

interface ConfigureAppStepProps {
  form: ReturnType<typeof useForm<ConfigureAppFormValues>>;
  supported_security_schemes: Record<string, { scope?: string }>;
  onNext: (values: ConfigureAppFormValues) => void;
  name: string;
  isLoading: boolean;
}

export function ConfigureAppStep({
  form,
  supported_security_schemes,
  onNext,
  name,
  isLoading,
}: ConfigureAppStepProps) {
  const currentSecurityScheme = form.watch("security_scheme");
  const { scope = "" } =
    supported_security_schemes?.[currentSecurityScheme] ?? {};
  const scopes = scope.split(/[\s,]+/).filter(Boolean);

  const [useACIDevOAuth2, setUseACIDevOAuth2] = useState(false);
  const clientId = form.watch("client_id");
  const clientSecret = form.watch("client_secret");

  const [isRedirectConfirmed, setIsRedirectConfirmed] = useState(false);
  const [isScopeConfirmed, setIsScopeConfirmed] = useState(false);

  const isFormValid = () => {
    if (currentSecurityScheme === "oauth2" && !useACIDevOAuth2) {
      return (
        !!clientId && !!clientSecret && isRedirectConfirmed && isScopeConfirmed
      );
    }
    return true;
  };

  // listen to security_scheme changes, reset form state when needed
  useEffect(() => {
    if (currentSecurityScheme !== "oauth2") {
      form.setValue("client_id", "");
      form.setValue("client_secret", "");
      setUseACIDevOAuth2(false);
      setIsRedirectConfirmed(false);
      setIsScopeConfirmed(false);
    }
  }, [currentSecurityScheme, form]);

  const handleSubmit = (values: ConfigureAppFormValues) => {
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

    onNext(values);
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
                        Copy and paste this URL into your OAuth2 app&apos;s
                        redirect/redirect URI settings
                      </TooltipContent>
                    </Tooltip>
                  </FormLabel>
                  <div className="pt-2">
                    <IdDisplay id={oauth2RedirectUrl} />
                  </div>
                  <div className="flex items-center gap-1">
                    <Checkbox
                      checked={isRedirectConfirmed}
                      onCheckedChange={(checked) =>
                        setIsRedirectConfirmed(checked === true)
                      }
                    />
                    <BsAsterisk className="h-2 w-2 text-red-500" />

                    <span className="text-xs">
                      I have added the above redirect URL to my OAuth2 app.
                    </span>
                  </div>
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
            <Button type="submit" disabled={isLoading || !isFormValid()}>
              {isLoading ? "Confirming..." : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </div>
  );
}
