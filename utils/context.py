from contextvars import ContextVar

current_user_id = ContextVar = ContextVar("current_user_id", default=None)

