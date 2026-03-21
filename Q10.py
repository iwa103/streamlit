import streamlit as st
import json
import streamlit.components.v1 as components

json_path = "10question.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("LLM テスト問題ツール")

if "index" not in st.session_state:
    st.session_state.index = 0

col1, col2 = st.columns(2)

with col1:
    if st.button("← 前の問題"):
        if st.session_state.index > 0:
            st.session_state.index -= 1

with col2:
    if st.button("次の問題 →"):
        if st.session_state.index < len(data) - 1:
            st.session_state.index += 1

qdata = data[st.session_state.index]

st.write(f"### 問題 {st.session_state.index+1} / {len(data)}")

st.write("### 問題")
st.text_area("question", qdata["question"], height=250)

# ★ ここがポイント（JSコピー）
copy_code = f"""
<div style="text-align:center;">
<button 
onclick="navigator.clipboard.writeText(`{qdata["question"]}`)"
style="
    font-size:22px;
    padding:12px 28px;
    background-color:#2196F3;
    color:white;
    border:none;
    border-radius:10px;
    cursor:pointer;
">
コピー
</button>
</div>
"""
components.html(copy_code, height=80)

st.write("### 正解")
st.write(qdata["answer"])
