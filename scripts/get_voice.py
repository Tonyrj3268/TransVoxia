import json
from collections import defaultdict
import requests

url = "https://api.play.ht/api/v1/getVoices"

headers = {
    "accept": "application/json",
    "AUTHORIZATION": "Bearer 6d1275331bc1403ebd28045f7b8d9f5e",
    "X-USER-ID": "9X30i7n3LMTk9OyzeTvSGxG9snO2",
}

response = requests.get(url, headers=headers)

# 使用defaultdict來收集同一語言的所有名稱
lang_dict = defaultdict(list)
for item in response.json()["voices"]:
    lang = item["language"]
    value = [item["value"], item["name"], "Chinese", item["sample"]]
    lang_dict[lang].append(value)

# 轉換為JSON並寫入文件
with open("voice.json", "w", encoding="utf-8") as f:
    json.dump(lang_dict, f, ensure_ascii=False, indent=4)
