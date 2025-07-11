export interface FunctionExecution {
  app_name: string;
  function_name: string;
  linked_account_owner_id: string;
  function_execution_start_time: string;
  function_execution_end_time: string;
  function_execution_duration: number;
  function_input: string;
  function_execution_result_success: boolean;
  function_execution_result_error: string | null;
  function_execution_result_data: string;
  function_execution_result_data_size: number;
}

export interface LogEntry {
  "@timestamp": string;
  level: string;
  message: string;
  function_execution: FunctionExecution;
  request_id: string;
  api_key_id: string;
  project_id: string;
  agent_id: string;
  org_id: string;
}

export interface LogSearchResponse {
  logs: LogEntry[];
  total_count: number;
  cursor: string | null;
}

export interface LogSearchParams {
  log_type?: string;
  project_id?: string;
  agent_id?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
  cursor?: string;
}
