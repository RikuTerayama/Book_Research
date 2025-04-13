import streamlit as st
import requests
import os
from dotenv import load_dotenv
from openai import OpenAI

# 環境変数読み込み
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Books API 呼び出し
def search_books_on_google(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    results = response.json()
    return results.get("items", [])

# ChatGPTで推薦キーワード生成（新バージョン対応）
def generate_book_keywords(user_input):
    prompt = f"以下の内容に関連する本を探したいので、検索に適したキーワードを3つ挙げてください。\n\n{user_input}\n"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# UI構築
st.title("📚 読みたい本、見つけよう")
user_input = st.text_input("今の気分・興味・学びたいことを入力してください")

if user_input:
    with st.spinner("AIが本を探しています..."):
        keywords = generate_book_keywords(user_input)
        books = search_books_on_google(keywords)

        st.markdown("### 🔍 関連する本の候補：")
        for book in books[:5]:  # 最初の5冊だけ表示
            info = book["volumeInfo"]
            title = info.get("title", "タイトル不明")
            authors = ", ".join(info.get("authors", ["著者情報なし"]))
            description = info.get("description", "説明なし")
            link = info.get("infoLink", "#")

            st.subheader(title)
            st.write(f"👤 著者: {authors}")
            st.write(f"📖 概要: {description[:300]}...")
            st.markdown(f"[🔗 詳細はこちら]({link})")
