import os
import openai


class TextGeneratorFactory:
    @staticmethod
    def create(is_pro_user):
        if is_pro_user:
            return TextGenerator("gpt-4-0613")
        else:
            return TextGenerator("gpt-3.5-turbo-16k")


class TextGenerator:
    def __init__(self, model_name):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name

    def generate_text(self, system_content, user_content):
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {
                        "role": "user",
                        "content": user_content,
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")  # Log the error
            raise  # Re-throw the error
