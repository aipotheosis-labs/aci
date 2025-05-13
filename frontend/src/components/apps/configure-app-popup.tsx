"use client";

import { ConfigureApp } from "@/components/apps/configure-app";

export interface ConfigureAppPopupProps {
  children: React.ReactNode;
  configureApp: (
    security_scheme: string,
    security_scheme_overrides?: {
      oauth2?: {
        client_id: string;
        client_secret: string;
      } | null;
    },
  ) => Promise<boolean>;
  name: string;
  supported_security_schemes: Record<string, { scope?: string }>;
  logo?: string;
}

export function ConfigureAppPopup(props: ConfigureAppPopupProps) {
  return <ConfigureApp {...props} />;
}
