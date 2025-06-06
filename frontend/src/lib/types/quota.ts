export interface QuotaUsage {
  projects: {
    used: number;
    limit: number;
  };

  linked_accounts: {
    used: number;
    limit: number;
  };

  agent_credentials: {
    used: number;
    limit: number;
  };

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
