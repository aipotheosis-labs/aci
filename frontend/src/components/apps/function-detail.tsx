"use client";
import ReactJson from "react-json-view";
import * as React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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

interface FunctionDetailProps {
  func: AppFunction;
}

export function FunctionDetail({ func }: FunctionDetailProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          See Details
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[625px]">
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
          <Tabs defaultValue="request">
            <TabsList>
              <TabsTrigger value="request">Request Schema</TabsTrigger>
              {/* <TabsTrigger value="response">Response Schema</TabsTrigger> */}
            </TabsList>
            <TabsContent value="request" className="mt-4">
              <ScrollArea className="h-96 rounded-md border p-4">
                <ReactJson name="parameters" src={func.parameters} />
              </ScrollArea>
            </TabsContent>
            {/* <TabsContent value="response" className="mt-4"></TabsContent> */}
          </Tabs>
        </div>
        <DialogFooter>
          {/* TODO: may need some buttons in the footer later */}
          {/* <Button variant="outline" type="button">
            Cancel
          </Button>
          <Button type="submit">Save</Button> */}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
