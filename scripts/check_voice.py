voice = [
    "cmn-TW-Standard-A",
    "cmn-TW-Standard-B",
    "cmn-TW-Standard-C",
    "cmn-TW-Wavenet-A",
    "cmn-TW-Wavenet-B",
    "cmn-TW-Wavenet-C",
    "zh-TW-HsiaoYuNeural",
    "zh-TW-HsiaoChenNeural",
    "zh-TW-YunJheNeural",
]

import requests

for i in voice:
    url = "https://api.play.ht/api/v1/convert/"

    payload = {"ssml": ['<speak><p>你好<break time="0.5s"/>我的朋友</p></speak>'], "voice": i}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer 6d1275331bc1403ebd28045f7b8d9f5e",
        "X-USER-ID": "9X30i7n3LMTk9OyzeTvSGxG9snO2",
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"聲音: {i}")
    print(response.text)
