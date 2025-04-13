from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_book_keywords(user_input):
    prompt = f"以下の内容に関連する本を探したいので、検索に適したキーワードを3つ挙げてください。\n\n{user_input}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()
