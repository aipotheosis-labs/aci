export interface LogEntry {
  id: string;
  timestamp: string;
  app_name: string;
  function_name: string;
  success: boolean;
  message: string;
  function_execution_app_name: string | null;
  function_execution_function_name: string | null;
  function_execution_input: string | null;
  function_execution_result_success: boolean | null;
  function_execution_result_error: string | null;
  function_execution_result_data: string | null;
}

export interface LogSearchResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  page_size: number;
}
