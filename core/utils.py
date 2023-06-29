from video.utils import process_transcript, process_synthesis
from audio.utils import process_audio
from translator.utils import process_deepl
from .decorators import TaskCancelledException
from .models import TaskStatus
import os
import errno


def process_task_notNeedModify(task):
    print(f"開始處理任務：{task.taskID}")
    status = TaskStatus.TASK_COMPLETED
    try:
        process_transcript(task)
        process_deepl(task)
        if task.mode in ["audio", "video"]:
            process_audio(task)
            if task.mode == "video":
                process_synthesis(task)

    except TaskCancelledException:
        status = TaskStatus.TASK_CANCELLED
        print(f"任務已被取消：{task.taskID}")
    except Exception as e:
        status = TaskStatus.TASK_FAILED
        print(f"強制結束任務：{task.taskID}, 錯誤：{str(e)}")
    finally:
        audioFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp3"
        videoFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp4"
        file_paths = [
            task.fileLocation,
            "translated/audio/" + audioFilePath,
            "translated/video/" + videoFilePath,
        ]
        deleteFile(file_paths)

    task.status = status
    task.save()
    print(f"結束處理任務：{task.taskID}")


def process_task_NeedModify(task):
    print(f"開始處理任務：{task.taskID}")
    status = TaskStatus.TASK_COMPLETED
    try:
        process_transcript(task)
        process_deepl(task)

    except TaskCancelledException:
        status = TaskStatus.TASK_CANCELLED
        print(f"任務已被取消：{task.taskID}")
    except Exception as e:
        status = TaskStatus.TASK_CANCELLED
        print(f"強制結束任務（生成文字稿）：{task.taskID}, 錯誤：{str(e)}")
    finally:
        file_paths = [task.fileLocation]
        deleteFile(file_paths)

    task.status = status
    task.save()
    print(f"結束處理任務：{task.taskID}")


def process_task_Remaining(task):
    print(f"開始處理剩餘任務：{task.taskID}")
    status = TaskStatus.TASK_COMPLETED
    try:
        process_audio(task)

        if task.mode == "video":
            process_synthesis(task)

    except TaskCancelledException:
        status = TaskStatus.TASK_CANCELLED
        print(f"任務已被取消：{task.taskID}")
    except Exception as e:
        status = TaskStatus.TASK_FAILED
        print(f"強制結束任務（生成文字稿）：{task.taskID}, 錯誤：{str(e)}")
    finally:
        audioFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp3"
        videoFilePath = (task.fileLocation).split("/")[-1].split(".")[0] + ".mp4"
        file_paths = [
            task.fileLocation,
            "translated/audio/" + audioFilePath,
            "translated/video/" + videoFilePath,
        ]
        deleteFile(file_paths)

    task.status = status
    task.save()
    print(f"結束處理任務：{task.taskID}")


def deleteFile(file_paths):
    for file_path in file_paths:
        try:
            os.remove(file_path)
            print(f"已成功刪除檔案：{file_path}")
        except OSError as e:
            if e.errno == errno.ENOENT:  # 檔案不存在的錯誤
                print(f"檔案不存在，無法刪除: {file_path}")
            elif e.errno == errno.EACCES:  # 檔案或目錄無法存取的錯誤
                print(f"檔案正在被使用，無法刪除: {file_path}")
            else:
                print(f"刪除檔案時發生錯誤: {file_path} - {str(e)}")
