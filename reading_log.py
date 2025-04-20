import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime

# --- Windowsの日本語フォント「メイリオ」を指定 ---
jp_font = fm.FontProperties(fname="C:\\Windows\\Fonts\\meiryo.ttc")

# --- データベース接続 ---
conn = sqlite3.connect("reading_log.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    genre TEXT,
    rating INTEGER,
    comment TEXT,
    read_time INTEGER,
    date_read DATE
)
""")
conn.commit()

# --- サイドバーで記録フォーム ---
st.sidebar.header("📚 本の記録を追加")
with st.sidebar.form("book_form"):
    title = st.text_input("タイトル")
    genre = st.selectbox("ジャンル", ["ビジネス", "小説", "ミステリー", "エッセイ", "自己啓発", "その他"])
    rating = st.slider("お気に入り度（1〜5）", 1, 5, 3)
    comment = st.text_area("コメント")
    read_time = st.number_input("読書時間（分）", min_value=0)
    date_read = st.date_input("読了日", value=datetime.today())
    submitted = st.form_submit_button("保存")

    if submitted:
        c.execute("INSERT INTO books (title, genre, rating, comment, read_time, date_read) VALUES (?, ?, ?, ?, ?, ?)",
                  (title, genre, rating, comment, read_time, date_read))
        conn.commit()
        st.sidebar.success("✅ 登録完了！")

# --- メイン画面 ---
st.title("📖 読書ログダッシュボード")
df = pd.read_sql_query("SELECT * FROM books", conn)

if not df.empty:
    df['date_read'] = pd.to_datetime(df['date_read'])
    df['month'] = df['date_read'].dt.to_period("M").astype(str)

    # 月別読書数
    st.subheader("📊 月別の読書数")

    # 対象期間の月リスト作成
    period_range = pd.period_range(start="2023-01", end="2025-12", freq="M").astype(str)
    monthly_df = pd.DataFrame({'month': period_range})

    # 実データの読書数集計
    df['month'] = df['date_read'].dt.to_period("M").astype(str)
    actual_counts = df.groupby('month').size().reset_index(name='count')

    # すべての月とマージ（存在しない月はNaN → 0に）
    merged = monthly_df.merge(actual_counts, on='month', how='left').fillna(0)
    merged['count'] = merged['count'].astype(int)
    merged.set_index('month', inplace=True)

    # グラフ描画
    st.bar_chart(merged)

    

    # ジャンル別割合
    st.subheader("📘 ジャンル別割合")
    genre_count = df['genre'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(
        genre_count,
        labels=genre_count.index,
        autopct='%1.1f%%',
        textprops={'fontproperties': jp_font}
    )
    ax.axis("equal")
    st.pyplot(fig)

    # --- 月別読書時間グラフの追加（2023年1月〜2025年12月） ---
    st.subheader("⏱ 月別の読書時間（分）")

    # 読書時間が記録された月ごとの合計
    actual_time = df.groupby('month')['read_time'].sum().reset_index(name='total_time')

    # 全期間の月とマージ
    merged_time = monthly_df.merge(actual_time, on='month', how='left').fillna(0)
    merged_time['total_time'] = merged_time['total_time'].astype(int)
    merged_time.set_index('month', inplace=True)

    # グラフ描画
    st.bar_chart(merged_time)

    # 読書履歴
    st.subheader("📚 読書履歴")
    for _, row in df.iterrows():
        st.markdown(f"### {row['title']}（⭐️ {row['rating']}/5）")
        st.write(f"ジャンル：{row['genre']}")
        st.write(f"読書時間：{row['read_time']}分")
        st.write(f"読了日：{row['date_read'].date()}")
        st.write(f"コメント：{row['comment']}")
        st.write("---")
else:
    st.info("まだ記録がありません📘")

conn.close()
