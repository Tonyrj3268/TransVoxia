from django.dispatch import Signal

# 開始產生文字稿
start_transcript_signal = Signal()

# 開始deepl翻譯
start_deepl_signal = Signal()