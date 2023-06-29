from functools import wraps
from .models import TaskStatus


class TaskCancelledException(Exception):
    pass


def check_task_status(func):
    @wraps(func)
    def wrapper(task, *args, **kwargs):
        result = func(task, *args, **kwargs)
        task.refresh_from_db()
        print(f"任務狀態：{task.status}")
        if task.status == TaskStatus.TASK_CANCELLED:
            raise TaskCancelledException("任务已被取消")
        return result

    return wrapper
