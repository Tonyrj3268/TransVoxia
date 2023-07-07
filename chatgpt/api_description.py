chat_view_set = """
這個API是一個聊天服務API，可以用來生成來自OpenAI的模型的自動回應。

你需要提供兩種訊息：

system_content: 這是系統的訊息，可以設定對話的情境。

user_content: 這是用戶的訊息，例如問題或指令。

系統會根據你的帳戶類型選擇OpenAI模型。一般帳戶用GPT-3.5模型，premium帳戶用GPT-4模型。

API會返回一個包含以下元素的JSON：

system_content: 你提供的系統訊息。

user_content: 你提供的用戶訊息。

response: OpenAI模型生成的回應。

如果處理過程出現錯誤，你會收到錯誤訊息。
"""
