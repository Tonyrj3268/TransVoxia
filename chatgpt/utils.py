import os
import openai


def chatgpt_repair(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
    )


# 使用chatgpt幫我生成修改後的文字稿
def generate_text(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a hilarious stand-up comedy creator who helped me rewrite my next verbatim article into a witty piece and translate it back into the original language.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")  # Log the error
        raise  # Re-throw the error
