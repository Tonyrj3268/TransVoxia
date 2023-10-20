from video.utils import process_transcript, process_synthesis
from audio.utils import process_audio, merge_audio_and_video, split_bg_music, auditok_detect,merge_audio_and_bgmusic
from translator.utils import process_deepl
from .decorators import TaskCancelledException
from .models import TaskStatus, Task
import os
import errno
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import traceback
import asyncio

def process_task_notNeedModify(task):
    raise Exception("it should not be used")
    # print(f"任務開始：{task.taskID}")
    # basename = task.get_file_basename()
    # file_paths = [
    #     task.fileLocation,
    #     "translated/audio/" + basename + ".mp3",
    #     "translated/video/" + basename + ".mp4",
    # ]
    # with handle_task_exceptions(task, file_paths):
    #     process_transcript(task)
    #     process_deepl(task)
    #     if task.mode in ["audio", "video"]:
    #         audio_file_paths = process_audio(task)
    #         merge_audio_and_video(task, audio_file_paths)
    #         if task.mode == "video":
    #             process_synthesis(task)
    #     task.status = TaskStatus.TASK_COMPLETED
    #     task.save()
    # print(f"結束處理任務：{task.taskID}")


def process_task_NeedModify(task):
    print(f"任務開始：{task.taskID}")
    file_paths = [
        task.fileLocation,
    ]

    with handle_task_exceptions(task, file_paths):
        process_transcript(task)
        process_deepl(task)
    task.status = TaskStatus.TASK_STOPPED
    task.save()


def process_task_Remaining(task:Task,voice_list:list[str]):
    print(f"開始處理剩餘任務：{task.taskID}")
    basename = task.get_file_basename()
    file_paths = [
        task.fileLocation,
        "translated/audio/" + basename + ".mp3",
        "translated/video/" + basename + ".mp4",
        "translated/bgmusic/mdx_extra/" + basename + "/no_vocals.mp3",
    ]

    with handle_task_exceptions(task, file_paths):
        audio_file_paths = asyncio.run(process_audio(task, voice_list))
        csv_list = []
        with ThreadPoolExecutor() as executor:
            for mp3_path, voice in zip(audio_file_paths, voice_list):
                csv = f"{os.path.splitext(mp3_path)[0]}.csv"
                csv_list.append(csv)
                executor.submit(
                    auditok_detect,
                    mp3_path,
                    csv,
                )
        bumusic_dir = f"translated/bgmusic"
        split_bg_music(task.fileLocation,output_dir=bumusic_dir)
        bumusic_path =os.path.join(bumusic_dir,"mdx_extra", f"{basename}/no_vocals.mp3")
        merge_audio_and_bgmusic(task, audio_file_paths, csv_list, bumusic_path)

        if task.mode == "video":
            process_synthesis(task)

        file_paths+=csv_list
        file_paths+=audio_file_paths
        file_paths.append(bumusic_dir+"/mdx_extra")
       
    task.status = TaskStatus.TASK_COMPLETED
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



@contextmanager
def handle_task_exceptions(task, file_paths):
    try:
        yield
    except TaskCancelledException:
        task.status = TaskStatus.TASK_CANCELLED
        task.save()
        print(f"任务取消：{task.taskID}")
    except Exception as e:
        task.status = TaskStatus.TASK_FAILED
        task.save()
        print(f"强制结束任务：{task.taskID}")
        print(traceback.format_exc())
    finally:
        print(f"清理任务")
        print(file_paths)
        deleteFile(file_paths)
