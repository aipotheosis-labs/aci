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
import { useState } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { BsQuestionCircle } from "react-icons/bs";
import { Badge } from "@/components/ui/badge";
import { IdDisplay } from "@/components/apps/id-display";

export const ConfigureAppFormSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
  client_id: z.string().optional().default(""),
  client_secret: z.string().optional().default(""),
});
export type ConfigureAppFormValues = z.infer<typeof ConfigureAppFormSchema>;

interface ConfigureAppStepProps {
  form: ReturnType<typeof useForm<ConfigureAppFormValues>>;
  security_schemes: string[];
  onNext: (values: ConfigureAppFormValues) => void;
  name: string;
  isLoading: boolean;
  redirectUrl: string;
  oauth2Scope?: string;
}

export function ConfigureAppStep({
  form,
  security_schemes,
  onNext,
  name,
  isLoading,
  redirectUrl,
  oauth2Scope,
}: ConfigureAppStepProps) {
  const [customOAuth2Credentials, setCustomOAuth2Credentials] = useState(false);
  const scopes = oauth2Scope?.split(" ") ?? [];

  // only split into two columns when oauth2 + custom toggled
  const isOAuth2Custom =
    form.watch("security_scheme") === "oauth2" && customOAuth2Credentials;

  const handleSubmit = (values: ConfigureAppFormValues) => {
    if (values.security_scheme === "oauth2" && customOAuth2Credentials) {
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
        <div className="p-3 border rounded-md bg-muted/30 flex items-center gap-3">
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
                    {security_schemes.map((scheme, idx) => (
                      <SelectItem key={idx} value={scheme}>
                        {scheme}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* OAuth2 Custom Toggle */}
          {form.watch("security_scheme") === "oauth2" && (
            <div className="flex items-center gap-2">
              <Switch
                checked={customOAuth2Credentials}
                onCheckedChange={setCustomOAuth2Credentials}
              />
              <Label>Use Your Own OAuth2 App</Label>
            </div>
          )}

          {customOAuth2Credentials && (
            <div
              className={`grid gap-6 ${isOAuth2Custom ? "lg:grid-cols-2" : ""}`}
            >
              {/* Left column: Read-only information */}
              <div className="space-y-6 min-w-0">
                {/* Redirect URL */}
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      Redirect URL
                    </span>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground cursor-pointer" />
                      </TooltipTrigger>
                      <TooltipContent>
                        Add this redirect URL in your OAuth2 app settings
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <IdDisplay id={redirectUrl} />
                </div>

                {/* Scope */}
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Scope
                    </span>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground cursor-pointer" />
                      </TooltipTrigger>
                      <TooltipContent>
                        Scopes requested by the OAuth2 provider
                      </TooltipContent>
                    </Tooltip>
                  </div>
                  <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
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
                </div>
              </div>

              {/* Right column: Input fields */}
              <div className="space-y-6 min-w-0">
                <FormField
                  control={form.control}
                  name="client_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>OAuth2 Client ID</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Client ID" />
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
                      <FormLabel>OAuth2 Client Secret</FormLabel>
                      <FormControl>
                        <Input
                          {...field}
                          type="password"
                          placeholder="Client Secret"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Confirming..." : "Confirm"}
            </Button>
          </DialogFooter>
        </form>
      </Form>
    </div>
  );
}
