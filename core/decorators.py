from functools import wraps
from .models import TaskStatus


class TaskCancelledException(Exception):
    pass


def check_task_status(status):  # 这里的status就是你想传入的参数
    def decorator(func):  # 这是一个新的装饰器函数，它接受被装饰的函数作为参数
        @wraps(func)
        def wrapper(task, *args, **kwargs):  # wrapper 现在只接受一个参数
            task.refresh_from_db()
            if task.status == TaskStatus.TASK_CANCELLED:
                raise TaskCancelledException("任务已被取消")
            task.status = status
            task.save()
            print(f"任務狀態：{task.get_status_display()}")
            result = func(task, *args, **kwargs)
            return result

        return wrapper

    return decorator
