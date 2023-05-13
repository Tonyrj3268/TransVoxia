import requests
import json
import time
from core.models import Task
from translator.models import Deepl
from video.models import Video
from .models import Play_ht


def process_audio(task: Task):
    text = Deepl.objects.get(taskID=task).translated_text
    voice = task.voice_selection
    origin_length = Video.objects.get(taskID=task).length

    url, dic = make_voice(text, voice, speed=100)
    length_ratio = round(dic["audioDuration"] / float(origin_length), 2)
    url_new, dic_new = make_voice(text, voice, speed=int(length_ratio * 100))

    Play_ht.objects.create(
        taskID=task,
        origin_audio_url=url,
        changed_audi_url=url_new,
        length_ratio=length_ratio,
        status=True,
    )
    task.status = "3"
    task.save()


def make_voice(text, voice, speed):
    payload = json.dumps(
        {
            "voice": voice,
            "content": [text],
            "title": "Testing public api convertion",
            "globalSpeed": str(speed) + "%",
        }
    )
    headers = {
        "Authorization": "27c66ac7aaf047449156d3494bcd04bf",
        "X-User-ID": "i7IAFc6EA2NJO6mgo6X3S5qwGso1",
        "Content-Type": "application/json",
    }
    response = requests.request(
        "POST", "https://play.ht/api/v1/convert", headers=headers, data=payload
    )
    id = response.json()["transcriptionId"]
    url = "https://play.ht/api/v1/articleStatus?transcriptionId=" + id
    print("----------生成聲音中----------" if speed == 1 else "----------加速聲音中----------")

    response = requests.request("GET", url, headers=headers)
    i = 0
    while (dic := check_voice_make(url)) == True:
        i += 1
        if i > 12:
            print("請求超時")
            break
    return url, dic


def check_voice_make(url):
    headers = {
        "Authorization": "27c66ac7aaf047449156d3494bcd04bf",
        "X-User-ID": "i7IAFc6EA2NJO6mgo6X3S5qwGso1",
        "Content-Type": "application/json",
    }
    response = requests.request("GET", url, headers=headers)
    dict_data = json.loads(
        response.text,
        object_pairs_hook=lambda x: {
            k: True if v == "true" else False if v == "false" else v for k, v in x
        },
    )
    if dict_data["message"] == "Transcription still in progress":
        print("請稍等")
        time.sleep(10)
        return True
    else:
        return dict_data
