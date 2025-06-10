export interface QuotaUsage {
  projects_used: number;
  linked_accounts_used: number;
  agent_credentials_used: number;
  plan: {
    name: string;
    features: {
      projects: number;
      linked_accounts: number;
      api_calls_monthly: number;
      agent_credentials: number;
      developer_seats: number;
      custom_oauth: boolean;
      log_retention_days: number;
    };
  };
}
