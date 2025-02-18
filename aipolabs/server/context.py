import contextvars

request_id_ctx_var = contextvars.ContextVar("request_id", default="unknown")
