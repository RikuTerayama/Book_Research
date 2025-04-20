import streamlit as st
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import time

# --- 環境変数の読み込み ---
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CALIL_APPKEY = os.environ.get("CALIL_APPKEY")

# --- OpenAI クライアント初期化 ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- ChatGPTでキーワード生成 ---
def generate_book_keywords(user_input):
    prompt = f"以下の内容に関連する本を探したいので、検索に適したキーワードを3つ挙げてください。キーワードのみを番号付きで挙げてください：\n\n{user_input}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- Google Books APIで本を検索 ---
def search_books_on_google(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    items = response.json().get("items", [])
    books = []
    for item in items[:5]:  # 上位5件だけ表示
        info = item.get("volumeInfo", {})
        title = info.get("title", "タイトル不明")
        authors = ", ".join(info.get("authors", ["著者不明"]))
        description = info.get("description", "説明なし")
        image = info.get("imageLinks", {}).get("thumbnail")
        link = info.get("infoLink", "")
        industry_ids = info.get("industryIdentifiers", [])
        isbn = next((i["identifier"] for i in industry_ids if i["type"] in ["ISBN_13", "ISBN_10"]), None)
        books.append({"title": title, "authors": authors, "description": description, "isbn": isbn, "image": image, "link": link})
    return books

# --- 蔵書検索API（カーリル） ---
def get_libraries(pref, city):
    url = "https://api.calil.jp/library"
    params = {
        "appkey": CALIL_APPKEY,
        "pref": pref,
        "city": city,
        "format": "json",
        "callback": "no"
    }
    resp = requests.get(url, params=params)
    return resp.json()

def check_book_availability(isbn, systemids):
    session_url = "https://api.calil.jp/check"
    params = {
        "appkey": CALIL_APPKEY,
        "isbn": isbn,
        "systemid": ",".join(systemids),
        "format": "json",
        "callback": "no"
    }
    r = requests.get(session_url, params=params)
    session_data = r.json()
    session_id = session_data.get("session")
    is_continue = session_data.get("continue", 1)

    while is_continue:
        time.sleep(1)
        poll_url = "https://api.calil.jp/check"
        poll_params = {
            "appkey": CALIL_APPKEY,
            "session": session_id,
            "format": "json",
            "callback": "no"
        }
        poll_resp = requests.get(poll_url, params=poll_params)
        session_data = poll_resp.json()
        is_continue = session_data.get("continue", 1)

    return session_data.get("books", {})

# --- Streamlit UI ---
st.title("読みたい本見つけよう")

with st.sidebar:
    keyword = st.text_input("キーワード（例：AI、経済）")  # 必須
    genre = st.text_input("ジャンル（例：ビジネス、哲学、小説）")  # 必須
    mood = st.text_input("気分（例：癒されたい）※任意")  # 任意
    detail = st.text_area("詳細テキスト　※任意")      # 任意

    pref = st.text_input("都道府県（例：東京都）")
    city = st.text_input("市区町村（例：中央区）")

# 🔽 ここから追記
    st.markdown("---")  # 区切り線（任意）

    dashboard_url = "https://nikkei.com"  # ← 遷移先URLに変更してください
    if st.button("ダッシュボードを見る"):
        st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{dashboard_url}\'" />', unsafe_allow_html=True)

if keyword and genre and pref and city:
    full_prompt = f"""本を探しています。
以下の情報を元に、関連書籍を見つけるための検索キーワードを3つ提案してください。
キーワードのみを番号付きで列挙してください。

【キーワード】{keyword}
【ジャンル】{genre}
【気分】{mood if mood else '指定なし'}
【補足テキスト】{detail if detail else 'なし'}
"""
    with st.spinner("AIがキーワードを生成しています..."):
        keywords = generate_book_keywords(full_prompt)

    with st.spinner("図書館を検索中..."):
        libraries = get_libraries(pref, city)
        public_libraries = [lib for lib in libraries if lib.get("category") in ["SMALL", "MEDIUM"]]

        if not public_libraries:
            st.warning("公共図書館が見つかりませんでした。")
            st.stop()

        systemids = list({lib["systemid"] for lib in public_libraries})
        libnames = [lib["short"] for lib in public_libraries]
        st.success(f"\U0001F4DA 検索対象の図書館（{len(libnames)}館）: {', '.join(libnames)}")

    with st.spinner("Google Booksで関連本を検索中..."):
        related_books = search_books_on_google(keywords)

    for book in related_books:
        title = book["title"]
        authors = book["authors"]
        description = book["description"]
        isbn = book["isbn"]
        image = book["image"]
        link = book["link"]

        st.subheader(title)
        st.write(f"👤 著者: {authors}")
        st.write(f"📖 概要: {description[:300]}...")
        if image:
            st.image(image, width=120)
        if link:
            st.markdown(f"[🔗 詳細はこちら]({link})")
        if isbn:
            with st.spinner(f"\U0001F50D ISBN {isbn} の蔵書状況を確認中..."):
                books = check_book_availability(isbn, systemids)
                found = False

                for bookid, bookinfo in books.items():
                    for sysid, sysdata in bookinfo.items():
                        libkey = sysdata.get("libkey", {})
                        st.write(f"🔎 {sysid} の蔵書情報: {libkey}")
                        available = [f"{name}（{status}）" for name, status in libkey.items() if status not in ["×", "不明", "-", "貸出中"]]
                        if available:
                            found = True
                            st.success(f"\U0001F3ED 所蔵あり: {', '.join(available)}")

                if not found:
                    st.write("\u274C 図書館での蔵書は見つかりませんでした")
        else:
            st.warning("ISBNが取得できなかったため、蔵書検索をスキップしました。")
