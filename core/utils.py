from video.utils import process_transcript, process_synthesis
from audio.utils import process_audio, merge_audio_and_video
from translator.utils import process_deepl
from .decorators import TaskCancelledException
from .models import TaskStatus, Task
import os
import errno
from contextlib import contextmanager

import demucs.separate
from concurrent.futures import ThreadPoolExecutor
import auditok
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
        "translated/bgmusic/" + basename + "/no_vocals.mp3",
    ]

    with handle_task_exceptions(task, file_paths):
        audio_file_paths = process_audio(task,voice_list)
        csv_list = []
        with ThreadPoolExecutor() as executor:
            for mp3, voice in zip(audio_file_paths, voice_list):
                csv = f"{os.path.splitext(mp3)[0]}_{voice}.csv"

                executor.submit(
                    auditok_detect,
                    mp3,
                    csv,
                )
                csv_list.append(csv)
        bumusic_dir = f"translated/bgmusic"
        split_bg_music(task.fileLocation,output_dir=bumusic_dir)
        bumusic_path =os.path.join(bumusic_dir, f"{basename}/no_vocals.mp3")
        merge_audio_and_video(task, audio_file_paths)
        if task.mode == "video":
            process_synthesis(task)

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


def split_bg_music(origin_mp4, output_dir):
    demucs.separate.main(
        [
            "--mp3",
            "--two-stems",
            "vocals",
            "-n",
            "mdx_extra",
            "-o",
            output_dir,
            origin_mp4,
        ]
    )

def auditok_detect(input_audio, output_csv):
    try:
        region = auditok.load(input_audio)
        audio_regions = list(
            region.split(
                max_dur=30,
                min_dur=0.3,
                max_silence=3,  # 設置為 2.5 秒以捕獲超過 3 秒的靜默區域
                energy_threshold=55,
            )
        )
        combined_entries = []
        for i, r in enumerate(audio_regions):
            # if i == 0 and need_split and r.meta.start > 0:
            #     combined_entries.append(
            #         {"start": 0, "end": round(r.meta.start, 2), "text": "---"}
            #     )
            begin = round(r.meta.start, 2)
            end = round(r.meta.end - 3, 2)
            if i == len(audio_regions) - 1:
                end = round(r.meta.end, 2)
            combined_entries.append({"start": begin, "end": end, "text": "xxx"})
            # if i != len(audio_regions) - 1 and end != audio_regions[i + 1].meta.start:
            #     combined_entries.append(
            #         {
            #             "start": end,
            #             "end": round(audio_regions[i + 1].meta.start, 2),
            #             "text": "---",
            #         }
            #     )

        formatted_entries_rounded = [
            (entry["start"], entry["end"], entry["text"].strip())
            for entry in combined_entries
        ]
        print(formatted_entries_rounded)
        with open(
            output_csv,
            "w",
            encoding="utf-8",
            newline=''
        ) as output_file:
            writer = csv.writer(output_file)
            for line in formatted_entries_rounded:
                writer.writerow(line)
    except Exception as e:
        print(e)

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
        print(f"强制结束任务：{task.taskID}，错误：{str(e)}")
    finally:
        deleteFile(file_paths)
