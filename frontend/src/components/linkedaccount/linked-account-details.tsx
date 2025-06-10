"use client";

import { useState } from "react";
import { LinkedAccount } from "@/lib/types/linkedaccount";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { EnhancedSwitch } from "@/components/ui-extensions/enhanced-switch/enhanced-switch";
import { formatToLocalTime } from "@/utils/time";
import { Copy, Check } from "lucide-react";

interface LinkedAccountDetailsProps {
  account: LinkedAccount;
  toggleAccountStatus?: (
    accountId: string,
    newStatus: boolean,
  ) => Promise<boolean>;
  children: React.ReactNode;
}

export function LinkedAccountDetails({
  account,
  toggleAccountStatus,
  children,
}: LinkedAccountDetailsProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyToken = async () => {
    if (account.security_credentials?.access_token) {
      try {
        await navigator.clipboard.writeText(
          account.security_credentials.access_token,
        );
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("Failed to copy token:", err);
      }
    }
  };

  const maskToken = (token: string) => {
    if (token.length <= 8) return "••••••••";
    return token.slice(0, 4) + "••••••••" + token.slice(-4);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader className="space-y-4">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl font-semibold">
              Linked Account Details
            </DialogTitle>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <Tabs defaultValue="account" className="w-full">
            <TabsList className="mb-2 bg-slate-200">
              {/* this button maybe should be active by default */}
              <TabsTrigger value="account">Account Info</TabsTrigger>
            </TabsList>

            <TabsContent value="account">
              <Card className="border rounded-md overflow-hidden">
                <Table>
                  <TableHeader className="bg-gray-50">
                    <TableRow>
                      <TableHead className="w-1/3 text-left">Key</TableHead>
                      <TableHead className="w-2/3 text-right">Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="text-gray-500">
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        Account Owner ID
                      </TableCell>
                      <TableCell className="text-right">
                        {account.linked_account_owner_id}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        App Name
                      </TableCell>
                      <TableCell className="text-right">
                        {account.app_name}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        Enabled
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end">
                          <EnhancedSwitch
                            checked={account.enabled}
                            onAsyncChange={async (checked) => {
                              if (toggleAccountStatus) {
                                return await toggleAccountStatus(
                                  account.id,
                                  checked,
                                );
                              }
                              return false;
                            }}
                            successMessage={(newState) => {
                              return `Linked account ${account.linked_account_owner_id} ${newState ? "enabled" : "disabled"}`;
                            }}
                            errorMessage="Failed to update linked account status"
                          />
                        </div>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        Security Scheme
                      </TableCell>
                      <TableCell className="text-right">
                        {account.security_scheme}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        Created at
                      </TableCell>
                      <TableCell className="text-right">
                        {formatToLocalTime(account.created_at)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium text-left">
                        Last Used At
                      </TableCell>
                      <TableCell className="text-right">
                        {account.last_used_at
                          ? formatToLocalTime(account.last_used_at)
                          : "Never"}
                      </TableCell>
                    </TableRow>
                    {account.security_credentials?.access_token && (
                      <TableRow>
                        <TableCell className="font-medium text-left">
                          Access Token
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                              {maskToken(
                                account.security_credentials.access_token,
                              )}
                            </code>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={handleCopyToken}
                              className="h-6 w-6 p-0"
                            >
                              {copied ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}
