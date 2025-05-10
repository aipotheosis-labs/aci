"use client";

import { ConfigureApp } from "@/components/apps/configure-app";

export interface ConfigureAppPopupProps {
  children: React.ReactNode;
  configureApp: (security_scheme: string) => Promise<boolean>;
  name: string;
  security_schemes: string[];
  logo?: string;
}

export function ConfigureAppPopup(props: ConfigureAppPopupProps) {
  return <ConfigureApp {...props} />;
}
