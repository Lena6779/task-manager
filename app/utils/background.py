"""Background tasks that run after a response has been sent."""

import logging

# Dedicated logger that writes user activity to activity.log
activity_logger = logging.getLogger("task_manager.activity")

# Guard so the file handler is only added once, even if imported repeatedly
if not activity_logger.handlers:
    handler = logging.FileHandler("activity.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    activity_logger.addHandler(handler)
    activity_logger.setLevel(logging.INFO)


def log_activity(user_id: int, action: str, detail: str = "") -> None:
    """Record a user action in activity.log.

    Scheduled with FastAPI's BackgroundTasks, so the client gets its
    response without waiting for the log write.
    """
    activity_logger.info("user=%s | action=%s | %s", user_id, action, detail)