export type LinkedAccount = {
  id: string;
  project_id: string;
  app_name: string;
  linked_account_owner_id: string;
  security_scheme: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string | null;
};
