"use client";
import ReactJsonView from "@microlink/react-json-view";
import * as React from "react";
import { useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { type AppFunction } from "@/lib/types/appfunction";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface FunctionDetailProps {
  func: AppFunction;
}

interface ParameterSchema {
  type: string;
  visible?: string[];
  properties?: Record<string, ParameterSchema>;
  required?: string[];
  description?: string;
  items?: ParameterSchema;
  enum?: [];
}

function isParameterSchema(value: unknown): value is ParameterSchema {
  return typeof value === "object" && value !== null && "type" in value;
}

enum FunctionDefinitionFormat {
  OPENAI = "openai",
  OPENAI_RESPONSES = "openai_responses",
  ANTHROPIC = "anthropic",
}

function filterVisibleProperties(
  parametersSchema: unknown,
): ParameterSchema | null {
  if (!isParameterSchema(parametersSchema)) {
    return null;
  }

  if (parametersSchema.type !== "object") {
    return parametersSchema;
  }

  const result = { ...parametersSchema };
  const visible = result.visible || [];
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { visible: _, ...resultWithoutVisible } = result;

  const properties = resultWithoutVisible.properties || {};
  const required = resultWithoutVisible.required || [];

  if (properties) {
    const filteredProperties: Record<string, ParameterSchema> = {};

    for (const key of visible) {
      if (properties[key]) {
        const filtered = filterVisibleProperties(properties[key]);
        if (filtered) {
          filteredProperties[key] = filtered;
        }
      }
    }

    resultWithoutVisible.properties = filteredProperties;
    resultWithoutVisible.required = required.filter((key) =>
      visible.includes(key),
    );
  }

  return resultWithoutVisible;
}

interface OpenAIFunctionDefinition {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: ParameterSchema;
  };
}

interface OpenAIResponsesFunctionDefinition {
  type: "function";
  name: string;
  description: string;
  parameters: ParameterSchema;
}

interface AnthropicFunctionDefinition {
  name: string;
  description: string;
  input_schema: ParameterSchema;
}

type FunctionDefinitionResult =
  | OpenAIFunctionDefinition
  | OpenAIResponsesFunctionDefinition
  | AnthropicFunctionDefinition
  | { error: string };

// Frontend implementation of format_function_definition consistent with backend
function formatFunctionDefinition(
  func: AppFunction,
  format: FunctionDefinitionFormat,
): FunctionDefinitionResult {
  // Filter visible properties in parameters
  const filteredParameters = filterVisibleProperties(func.parameters);

  if (!filteredParameters) {
    return { error: "Invalid parameters schema" };
  }

  switch (format) {
    case FunctionDefinitionFormat.OPENAI:
      return {
        type: "function",
        function: {
          name: func.name,
          description: func.description,
          parameters: filteredParameters,
        },
      };
    case FunctionDefinitionFormat.OPENAI_RESPONSES:
      return {
        type: "function",
        name: func.name,
        description: func.description,
        parameters: filteredParameters,
      };
    case FunctionDefinitionFormat.ANTHROPIC:
      return {
        name: func.name,
        description: func.description,
        input_schema: filteredParameters,
      };
    default:
      return {
        error: "Unknown format",
      };
  }
}

export function FunctionDetail({ func }: FunctionDetailProps) {
  const [selectedFormat, setSelectedFormat] =
    useState<FunctionDefinitionFormat>(FunctionDefinitionFormat.OPENAI);

  const formattedDefinition = useMemo(
    () => formatFunctionDefinition(func, selectedFormat),
    [func, selectedFormat],
  );

  const handleFormatChange = (value: string) => {
    setSelectedFormat(value as FunctionDefinitionFormat);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          See Details
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[625px] max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Function Details</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="text-sm font-medium text-muted-foreground">
                Function Name
              </div>
              <div className="w-fit bg-muted px-2 py-1 rounded-md">
                {func.name}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-sm font-medium text-muted-foreground">
                Description
              </div>
              <div className="bg-muted px-2 py-1 rounded-md">
                {func.description}
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground">
              Function Definition Format
            </div>
            <Select value={selectedFormat} onValueChange={handleFormatChange}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select Function Definition Format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={FunctionDefinitionFormat.OPENAI}>
                  OpenAI Completion
                </SelectItem>
                <SelectItem value={FunctionDefinitionFormat.OPENAI_RESPONSES}>
                  OpenAI Responses
                </SelectItem>
                <SelectItem value={FunctionDefinitionFormat.ANTHROPIC}>
                  Anthropic
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <ScrollArea className="h-96 rounded-md border p-4">
            <ReactJsonView name={false} src={formattedDefinition} />
          </ScrollArea>
        </div>
        <DialogFooter></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
