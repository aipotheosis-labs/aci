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

// Form schema for security scheme selection
export const securitySchemeFormSchema = z.object({
  security_scheme: z.string().min(1, "Security Scheme is required"),
});

export type SecuritySchemeFormValues = z.infer<typeof securitySchemeFormSchema>;

interface SecuritySchemeStepProps {
  form: ReturnType<typeof useForm<SecuritySchemeFormValues>>;
  security_schemes: string[];
  onNext: (values: SecuritySchemeFormValues) => void;
  onCancel: () => void;
  name: string;
}

export function SecuritySchemeStep({
  form,
  security_schemes,
  onNext,
  onCancel,
  name,
}: SecuritySchemeStepProps) {
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
                    {security_schemes.map((scheme, index) => (
                      <SelectItem key={index} value={scheme}>
                        {scheme}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit">Next</Button>
          </DialogFooter>
        </form>
      </Form>
    </div>
  );
}
