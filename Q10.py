import streamlit as st
import json
import pyperclip

# JSONファイルパス（Windows）
json_path = r"10question.json"
#json_path = r"D:\LLM\性能確認用データセット\Q10評価\10question.json"


# JSON読み込み
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("LLM テスト問題ツール")

# 初期問題
if "index" not in st.session_state:
    st.session_state.index = 0

# 前後ボタン
col1, col2 = st.columns(2)

with col1:
    if st.button("← 前の問題"):
        if st.session_state.index > 0:
            st.session_state.index -= 1

with col2:
    if st.button("次の問題 →"):
        if st.session_state.index < len(data) - 1:
            st.session_state.index += 1

# 現在の問題
qdata = data[st.session_state.index]

st.write(f"### 問題 {st.session_state.index+1} / {len(data)}")

st.write("### 問題")

# 改行付き表示
st.text_area("question", qdata["question"], height=250)

# コピー
if st.button("問題をコピー"):
    pyperclip.copy(qdata["question"])
    st.success("コピーしました")

# 正解
st.write("### 正解")
st.write(qdata["answer"])
