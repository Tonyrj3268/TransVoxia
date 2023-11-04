import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Trans_Voxia.settings")
application = get_wsgi_application()

from audio.models import Play_ht_voices, LanguageMapping

voices = Play_ht_voices.objects.all()[8:]
print(voices)

import requests

for i in voices:
    url = "https://api.play.ht/api/v1/convert/"

    payload = {
        "ssml": ['<speak><p>HI<break time="0.5s"/>my friend</p></speak>'],
        "voice": i.voice,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer 6d1275331bc1403ebd28045f7b8d9f5e",
        "X-USER-ID": "9X30i7n3LMTk9OyzeTvSGxG9snO2",
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"聲音: {i.voice}")
    print(response.text)
