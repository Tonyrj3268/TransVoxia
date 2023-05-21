# settings_fake.py

from .settings import *

# 覆蓋原始設定

# 應用程式設定
INSTALLED_APPS += [
    # 添加您的假視圖所在的應用程式
    "fake_api.apps.FakeApiConfig",
]

# 路由設定
ROOT_URLCONF = "Graduation_Project.fake_urls"

# 調整其他設定，例如資料庫、時區、靜態檔案路徑等，根據您的需求進行修改
# ...

# 假視圖端口設定
PORT = 8001  # 或您喜歡的其他端口號
