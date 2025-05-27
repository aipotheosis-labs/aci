import contextvars
from uuid import UUID

request_id_ctx_var = contextvars.ContextVar[str | None]("request_id", default="unknown")
agent_id_ctx_var = contextvars.ContextVar[UUID | None]("agent_id", default=None)
api_key_id_ctx_var = contextvars.ContextVar[UUID | None]("api_key_id", default=None)
project_id_ctx_var = contextvars.ContextVar[UUID | None]("project_id", default=None)
org_id_ctx_var = contextvars.ContextVar[UUID | None]("org_id", default=None)
