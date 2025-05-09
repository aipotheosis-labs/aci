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
export const ConfigureAppFormSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
});
import { IdDisplay } from "@/components/apps/id-display";

export type ConfigureAppFormValues = z.infer<typeof ConfigureAppFormSchema>;

interface ConfigureAppStepProps {
  form: ReturnType<typeof useForm<ConfigureAppFormValues>>;
  security_schemes: string[];
  onNext: (values: ConfigureAppFormValues) => void;
  name: string;
  isLoading: boolean;
  redirectUrl: string; // pass this in from parent
}

export function ConfigureAppStep({
  form,
  security_schemes,
  onNext,
  name,
  isLoading,
  redirectUrl,
}: ConfigureAppStepProps) {
  const [customOAuth2Credentials, setCustomOAuth2Credentials] = useState(false);

  return (
    <div className="space-y-4">
      <div className="mb-1">
        <div className="text-sm font-medium mb-2">API Provider</div>
        <div className="p-3 border rounded-md bg-muted/30 flex items-center gap-3">
          <span className="font-medium">{name}</span>
        </div>
      </div>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onNext)} className="space-y-4">
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
            <div className="space-y-4">
              {/* 1. Redirect URL as read-only display with tooltip */}
              <div className="flex items-center gap-2 w-[70%]">
                <span className="text-sm font-medium text-gray-500 w-24 shrink-0">
                  Redirect URL
                </span>

                <div className="flex items-center flex-1 gap-2 min-w-0">
                  <IdDisplay id={redirectUrl} />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="cursor-pointer">
                        <BsQuestionCircle className="h-4 w-4 text-muted-foreground" />
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      Add this redirect URL to your OAUTH2 App
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>

              {/* 2. Client ID only */}
              <FormItem>
                <FormLabel>OAuth2 Client ID</FormLabel>
                <FormControl>
                  <Input type="text" placeholder="Client ID" />
                </FormControl>
              </FormItem>

              {/* (Keep client secret if you still need it) */}
              <FormItem>
                <FormLabel>OAuth2 Client Secret</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Client Secret" />
                </FormControl>
              </FormItem>
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
